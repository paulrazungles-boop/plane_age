#!/usr/bin/env python3
# age_avion_app.py
# Integrated app: AvioADSB lookup + airlines DB parsing + age->"human age" model + Tkinter GUI
# Save this file and run with: python age_avion_app.py
# Requirements: requests, tkinter (standard), optionally PyPDF2 for parsing PDF airline DB

import os
import json
import time
import requests
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog

# Optional PDF parsing
try:
    import PyPDF2
    HAVE_PYPDF2 = True
except Exception:
    HAVE_PYPDF2 = False

# ===== CONFIG =====
CACHE_FILE = "cache_avions.json"
CACHE_DURATION = 3600  # 1 hour by default
AIRLINES_DB_TXT = "airlines_db.txt"  # fallback text file (if you exported the PDF as text)
AIRLINES_PDF_CANDIDATES = [
    "/mnt/data/Airlines_codes.pdf",
    "/mnt/data/Airlines_codes(1).pdf",
    "/mnt/data/Airlines_codes.txt",
    "/mnt/data/Fichier markdown(4).md",
    "/mnt/data/Fichier markdown(3).md",
]


# ===== CACHE HELPERS =====
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


# ===== AIRLINES DB LOADING =====
def parse_lines_for_airlines(lines):
    airlines = {}
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        # heuristics: last token of the line is often the 2-letter IATA code
        last = parts[-1]
        if len(last) in (2, 3) and last.isalnum():
            code = last
            name = " ".join(parts[:-1])
            if name:
                airlines[name.lower()] = code.upper()
    return airlines


def load_airlines_from_pdf(path):
    airlines = {}
    if not HAVE_PYPDF2:
        print("PyPDF2 non installé: impossible d'extraire le PDF automatiquement.")
        return airlines
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            lines = []
            for p in reader.pages:
                try:
                    txt = p.extract_text()
                except Exception:
                    txt = ""
                if txt:
                    for ln in txt.splitlines():
                        lines.append(ln)
            airlines = parse_lines_for_airlines(lines)
    except Exception as e:
        print("Erreur lecture PDF:", e)
    return airlines


def load_airlines_from_text(path):
    airlines = {}
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            airlines = parse_lines_for_airlines(lines)
    except Exception as e:
        print("Erreur lecture fichier texte:", e)
    return airlines


def try_load_airlines_db():
    # Try multiple candidate files (uploaded by user)
    for p in AIRLINES_PDF_CANDIDATES:
        if os.path.exists(p):
            if p.lower().endswith(".pdf"):
                print("Chargement base compagnies depuis PDF:", p)
                db = load_airlines_from_pdf(p)
                if db:
                    return db
            else:
                print("Chargement base compagnies depuis fichier texte/markdown:", p)
                db = load_airlines_from_text(p)
                if db:
                    return db
    # fallback if user exported a text file next to the script
    if os.path.exists(AIRLINES_DB_TXT):
        return load_airlines_from_text(AIRLINES_DB_TXT)
    return {}


# ===== AVIOADSB API (no key required) =====
def get_aircraft_data_from_avio(registration):
    registration = registration.strip().upper()
    if not registration:
        return None

    cache = load_cache()
    # Use cache key prefix to avoid collision with airline DB entries
    cache_key = f"reg:{registration}"
    if cache_key in cache:
        data, ts = cache[cache_key]
        if time.time() - ts < CACHE_DURATION:
            return data

    url = f"https://avioadsb.org/v1/reg/{registration}"

    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            print("AvioADSB API status:", r.status_code)
            return None
        j = r.json()
        if not j.get("ac"):
            return None
        ac = j["ac"][0]
        result = {
            "type": ac.get("t") or ac.get("model") or "UNKNOWN",
            "callsign": ac.get("flight") or ac.get("call") or "",
            "registration": ac.get("r") or registration,
            "hex": ac.get("hex") or "",
        }
        cache[cache_key] = (result, time.time())
        save_cache(cache)
        return result
    except Exception as e:
        print("Erreur AvioADSB:", e)
        return None


# ===== MODEL FUNCTIONS (from earlier) =====
def get_alpha(category):
    category = category.lower()
    if category == "ga":
        return 1.15, 20000
    elif category == "narrow":
        return 2.0, 60000
    elif category == "wide":
        return 1.7, 40000
    elif category == "super":
        return 1.6, 35000
    return 2.0, 60000


def get_maintenance_factor(level):
    level = level.lower()
    return {
        "excellente": 0.7,
        "bonne": 0.85,
        "normale": 1.0,
        "mauvaise": 1.3
    }.get(level, 1.0)


def calcul_age_humain(age, cycles, category, maintenance):
    alpha, cycles_max = get_alpha(category)
    M = get_maintenance_factor(maintenance)
    try:
        age_humain = alpha * (age ** 0.9) * (1 + 0.8 * (cycles / cycles_max) * M)
    except Exception:
        age_humain = alpha * (age ** 0.9)
    return round(age_humain, 1)


def estimate_cycles(age, category):
    category = category.lower()
    if category == "ga":
        return int(age * 200)
    elif category == "narrow":
        return int(age * 1000)
    elif category == "wide":
        return int(age * 600)
    elif category == "super":
        return int(age * 500)
    return int(age * 800)


# ===== airline-based cycle estimation =====
def estimate_cycles_by_airline(age, category, airline_code):
    if not airline_code:
        return estimate_cycles(age, category)
    # normalize
    ac = airline_code.upper()
    low_cost = {"FR", "U2", "W6", "VY", "RY"}  # includes Ryanair-like codes; RY is often registry not IATA but keep safe
    legacy = {"AF", "LH", "BA", "KL", "AA", "DL", "UA", "AC"}
    cargo = {"FX", "5X", "CV"}
    regional = {"YW", "QK", "YX", "S5"}

    if ac in low_cost:
        return int(age * 1200)
    elif ac in legacy:
        return int(age * 900)
    elif ac in cargo:
        return int(age * 800)
    elif ac in regional:
        return int(age * 700)
    else:
        return estimate_cycles(age, category)


# ===== aircraft type -> category mapping (improved) =====
def detect_category_from_type(aircraft_type):
    t = (aircraft_type or "").upper()

    # small GA piston / light
    if any(x in t for x in ["C172", "PA28", "DR40", "SR22", "C182", "PIPER", "CESSNA"]):
        return "ga"

    # regional / small airliners / A220 fits here
    if any(x in t for x in ["A220", "A318", "A319", "A320", "A321", "B737", "E170", "E175", "E190", "E195", "CRJ", "AT72", "AT43", "AT45"]):
        return "narrow"

    # widebodies and long range
    if any(x in t for x in ["A300", "A310", "A330", "A340", "A350", "B767", "B777", "B787", "777", "787", "330", "350"]):
        return "wide"

    # very large
    if any(x in t for x in ["A380", "B747"]):
        return "super"

    # fallback: if string contains numbers and letters typical of airliner, treat as narrow
    if any(ch.isdigit() for ch in t) and any(ch.isalpha() for ch in t):
        return "narrow"
    return "narrow"


# ===== maintenance estimate from airline code (then confirm) =====
def estimate_maintenance(airline_code):
    if not airline_code:
        base = "normale"
    else:
        ac = airline_code.upper()
        good = {"AF", "LH", "BA", "KL", "SQ", "NH"}
        low_cost = {"FR", "U2", "W6", "VY"}
        if ac in good:
            base = "bonne"
        elif ac in low_cost:
            base = "normale"
        else:
            base = "normale"
    return base


# ===== Utilities =====
def detect_airline_from_callsign(callsign):
    if not callsign:
        return None
    # callsign often begins with airline prefix (IATA 2-letter or airline designator). Heuristic: first 2 letters/digits
    cs = callsign.strip().upper()
    # Some callsigns contain letters and numbers; take up to first 3 letters/digits chunk
    prefix = "".join(ch for ch in cs if ch.isalnum())[:2]
    if prefix:
        return prefix.upper()
    return None


# ===== GUI Application =====
class AgeAvionApp:
    def __init__(self, root):
        self.root = root
        root.title("Age humain d'un avion - App")
        self.airlines_db = try_load_airlines_db()
        if self.airlines_db:
            print(f"Base compagnies chargée ({len(self.airlines_db)} entrées).")
        else:
            print("Aucune base compagnies chargée automatiquement. Vous pouvez charger un fichier via le bouton.")

        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Immatriculation (ex: F-GKXA) :").grid(row=0, column=0, sticky="w")
        self.entry_reg = tk.Entry(frame, width=20)
        self.entry_reg.grid(row=0, column=1, sticky="w")

        tk.Button(frame, text="Chercher (AvioADSB)", command=self.lookup).grid(row=0, column=2, padx=5)

        tk.Label(frame, text="Type avion détecté :").grid(row=1, column=0, sticky="w")
        self.var_type = tk.StringVar(value="N/A")
        tk.Label(frame, textvariable=self.var_type).grid(row=1, column=1, sticky="w")

        tk.Label(frame, text="Compagnie détectée (IATA tentative) :").grid(row=2, column=0, sticky="w")
        self.var_airline = tk.StringVar(value="N/A")
        tk.Label(frame, textvariable=self.var_airline).grid(row=2, column=1, sticky="w")

        tk.Label(frame, text="Categorie (auto) :").grid(row=3, column=0, sticky="w")
        self.var_cat = tk.StringVar(value="N/A")
        tk.Label(frame, textvariable=self.var_cat).grid(row=3, column=1, sticky="w")

        tk.Label(frame, text="Age avion (années) :").grid(row=4, column=0, sticky="w")
        self.entry_age = tk.Entry(frame, width=10)
        self.entry_age.grid(row=4, column=1, sticky="w")

        tk.Label(frame, text="Cycles (ou 'auto') :").grid(row=5, column=0, sticky="w")
        self.entry_cycles = tk.Entry(frame, width=20)
        self.entry_cycles.insert(0, "auto")
        self.entry_cycles.grid(row=5, column=1, sticky="w")

        tk.Label(frame, text="Maintenance (excellente/bonne/normale/mauvaise) :").grid(row=6, column=0, sticky="w")
        self.maint_var = tk.StringVar(value="normale")
        tk.OptionMenu(frame, self.maint_var, "excellente", "bonne", "normale", "mauvaise").grid(row=6, column=1, sticky="w")

        tk.Button(frame, text="Charger base compagnies...", command=self.cmd_load_airlines).grid(row=7, column=0, pady=8)
        tk.Button(frame, text="Calculer age humain", command=self.cmd_calculate).grid(row=7, column=1, pady=8)
        tk.Button(frame, text="Exporter résultat JSON", command=self.cmd_export).grid(row=7, column=2, pady=8)

        self.var_result = tk.StringVar(value="Résultat ici")
        tk.Label(frame, textvariable=self.var_result, justify="left").grid(row=8, column=0, columnspan=3, sticky="w")

    def cmd_load_airlines(self):
        path = filedialog.askopenfilename(title="Choisir fichier base compagnies (txt ou pdf)")
        if not path:
            return
        if path.lower().endswith(".pdf"):
            db = load_airlines_from_pdf(path) if HAVE_PYPDF2 else {}
        else:
            db = load_airlines_from_text(path)
        if not db:
            messagebox.showwarning("Base compagnies", "Aucune entrée trouvée dans ce fichier")
            return
        self.airlines_db = db
        messagebox.showinfo("Base compagnies", f"Base chargée ({len(db)} entrées)")

    def lookup(self):
        reg = self.entry_reg.get().strip().upper()
        if not reg:
            messagebox.showwarning("Immatriculation", "Veuillez saisir une immatriculation")
            return
        data = get_aircraft_data_from_avio(reg)
        if not data:
            messagebox.showwarning("Recherche", "Aucun résultat trouvé via AvioADSB")
            return
        atype = data.get("type", "UNKNOWN")
        callsign = data.get("callsign", "")
        self.var_type.set(atype)
        airline_guess = detect_airline_from_callsign(callsign) or ""
        self.var_airline.set(airline_guess or "N/A")

        # auto category based on type -> and show to user
        cat = detect_category_from_type(atype)
        self.var_cat.set(cat)

        # pre-fill maintenance by estimating from airline if possible
        est_maint = estimate_maintenance(airline_guess)
        self.maint_var.set(est_maint)

    def cmd_calculate(self):
        # Get inputs
        reg = self.entry_reg.get().strip().upper()
        age_text = self.entry_age.get().strip()
        if not age_text:
            messagebox.showwarning("Age", "Saisis l'âge de l'avion en années")
            return
        try:
            age = float(age_text)
        except:
            messagebox.showerror("Age", "L'âge doit être un nombre (années)")
            return

        # try retrieving fetched type/airline
        atype = self.var_type.get() if self.var_type.get() != "N/A" else None
        airline_guess = self.var_airline.get() if self.var_airline.get() != "N/A" else None

        # determine category (auto or let user override)
        if atype:
            detected_cat = detect_category_from_type(atype)
        else:
            detected_cat = simpledialog.askstring("Catégorie", "Type inconnu. Entrer la catégorie (ga/narrow/wide/super):", initialvalue="narrow")
            if not detected_cat:
                detected_cat = "narrow"

        # If airlines DB present, try to map full company name if callsign missing
        airline_code = airline_guess
        if (not airline_code or airline_code == "None") and self.airlines_db and reg:
            # try to match registration to DB by searching values? fallback not great
            # We keep airline_code as None if no callsign
            airline_code = None

        # cycles: auto or manual, but if auto and airline_code available, use airline-based estimation with confirmation
        cycles_input = self.entry_cycles.get().strip().lower()
        if cycles_input == "auto":
            cycles_est = estimate_cycles_by_airline(age, detected_cat, airline_code)
            # Ask confirmation
            user = simpledialog.askstring("Cycles estimés", f"Cycles estimés: {cycles_est}. Confirmer ou saisir une autre valeur? (laisser vide pour confirmer)")
            if user and user.strip():
                try:
                    cycles = int(user.strip())
                except:
                    messagebox.showerror("Cycles", "Valeur cycles invalide. On prend l'estimation.")
                    cycles = cycles_est
            else:
                cycles = cycles_est
        else:
            try:
                cycles = int(cycles_input)
            except:
                messagebox.showerror("Cycles", "Entrée cycles invalide. Utilisation de 'auto'")
                cycles = estimate_cycles(age, detected_cat)

        # maintenance: prefilled but ask confirmation
        maint_prefill = self.maint_var.get()
        user_maint = simpledialog.askstring("Maintenance", f"Maintenance estimée: {maint_prefill}. Confirmer ou modifier (excellente/bonne/normale/mauvaise)?")
        if user_maint and user_maint.strip():
            maintenance = user_maint.strip().lower()
        else:
            maintenance = maint_prefill.lower()

        # compute
        human_age = calcul_age_humain(age, cycles, detected_cat, maintenance)

        # prepare result text and store in cache file for later export
        result_obj = {
            "registration": reg,
            "type": atype,
            "callsign_guess": airline_guess,
            "category": detected_cat,
            "age_years": age,
            "cycles_used": cycles,
            "maintenance": maintenance,
            "age_human": human_age,
            "timestamp": int(time.time())
        }

        # store ephemeral in cache as recent query
        cache = load_cache()
        cache_key = f"query:{reg or str(time.time())}"
        cache[cache_key] = (result_obj, time.time())
        save_cache(cache)

        # display
        display = (
            f"Type: {atype}\\n"
            f"Category: {detected_cat}\\n"
            f"Age avion: {age} ans\\n"
            f"Cycles considérés: {cycles}\\n"
            f"Maintenance: {maintenance}\\n"
            f"\\n=> Âge humain estimé: {human_age} ans"
        )
        self.var_result.set(display)

    def cmd_export(self):
        cache = load_cache()
        # gather recent query entries
        results = [v[0] for k, v in cache.items() if k.startswith("query:")]
        if not results:
            messagebox.showinfo("Export", "Aucun résultat à exporter (exécute un calcul d'abord).")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON file","*.json")], title="Enregistrer résultats JSON")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Export", f"Exporté {len(results)} résultats vers {path}")
        except Exception as e:
            messagebox.showerror("Export", f"Erreur lors de l'export: {e}")


def main():
    root = tk.Tk()
    app = AgeAvionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
