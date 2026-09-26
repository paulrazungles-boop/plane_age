#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
  AGE AVION -> AGE HUMAIN
=====================================================================
Application de bureau (Tkinter) qui estime l'"âge humain" d'un avion
à partir de :
    - son âge réel (années)
    - son type (catégorie : GA / monocouloir / long-courrier / très
      gros porteur), déduit automatiquement du code ICAO de l'avion
    - son exploitant (compagnie), déduit automatiquement du code
      IATA ou ICAO de la compagnie -> décide du "type d'activité"
      (low-cost, legacy, cargo, régionale, charter...) et de la
      "qualité de maintenance" par défaut
    - dans tous les cas, TOUT reste modifiable manuellement (aucun
      champ n'est verrouillé), en particulier si l'avion est classé
      en Aviation Générale (GA) où l'on choisit alors une intensité
      d'utilisation (intensive / moyenne / faible) plutôt qu'une
      compagnie.

CHANGEMENTS PAR RAPPORT A LA VERSION PRECEDENTE
------------------------------------------------
- Suppression totale du module "requests" / de l'appel API (ne
  fonctionnait pas) : plus aucun accès réseau n'est nécessaire.
- Suppression de toutes les boîtes de dialogue (messagebox,
  simpledialog) : tout se passe dans la fenêtre principale, avec des
  messages de statut affichés directement dans l'interface.
- Bases de données "compagnies" et "types d'avions" embarquées dans
  le script (voir plus bas), construites à partir des listes de
  codes IATA/ICAO fournies, et enrichissables via deux fichiers CSV
  optionnels placés à côté du script (voir section EXTENSIBILITE).
- Le "type d'activité" et la "qualité de maintenance" sont proposés
  automatiquement dès qu'une compagnie est reconnue, mais restent
  toujours modifiables à la main.
- Ajout du mode "Aviation Générale" avec 3 niveaux d'intensité
  d'utilisation (intensive / moyenne / faible), utilisés à la place
  d'une compagnie pour estimer le nombre de cycles.

IDEES SUPPLEMENTAIRES INCLUSES DANS CE FICHIER
------------------------------------------------
1. Champ "cycles totaux personnalisés" : si vous connaissez le
   nombre réel de cycles (décollages/atterrissages) de l'avion, vous
   pouvez le saisir directement au lieu de laisser l'appli l'estimer.
2. Verdict qualitatif + code couleur selon l'âge humain obtenu
   (jeune / mûr / senior / très âgé / "bon pour le musée").
3. Historique des calculs de la session, affiché dans un tableau en
   bas de fenêtre (comparer plusieurs avions sans rien perdre).
4. Export du résultat courant vers un fichier texte
   ("resultats_age_avion.txt", à côté du script) sans passer par une
   boîte de dialogue d'enregistrement.
5. Champ "immatriculation" facultatif, uniquement pour vos notes
   dans l'historique (n'influence pas le calcul).
6. Mécanisme d'extension par CSV pour compléter vous-même, au fil du
   temps, les bases compagnies / types d'avions (utile car la base
   officielle ICAO Doc 8643 complète n'est pas librement
   téléchargeable - voir note en fin de fichier).

=====================================================================
"""

import os
import csv
import time
import tkinter as tk
from tkinter import ttk

# =====================================================================
#  1. BASE DE DONNEES "COMPAGNIES AERIENNES"
#     (code IATA, code ICAO, nom, catégorie)
#     catégorie parmi : lowcost / legacy / cargo / regional / charter / other
# =====================================================================

AIRLINES_RAW = [
    # --- Low-cost ---------------------------------------------------
    ("FR", "RYR", "Ryanair", "lowcost"),
    ("U2", "EZY", "easyJet", "lowcost"),
    ("W6", "WZZ", "Wizz Air", "lowcost"),
    ("VY", "VLG", "Vueling Airlines", "lowcost"),
    ("V7", "VOE", "Volotea", "lowcost"),
    ("DY", "NAX", "Norwegian Air Shuttle", "lowcost"),
    ("EW", "EWG", "Eurowings", "lowcost"),
    ("WN", "SWA", "Southwest Airlines", "lowcost"),
    ("NK", "NKS", "Spirit Airlines", "lowcost"),
    ("F9", "FFT", "Frontier Airlines", "lowcost"),
    ("G4", "AAY", "Allegiant Air", "lowcost"),
    ("B6", "JBU", "jetBlue Airways", "lowcost"),
    ("SY", "SCX", "Sun Country Airlines", "lowcost"),
    ("G3", "GLO", "Gol Linhas Aereas", "lowcost"),
    ("AD", "AZU", "Azul Linhas Aereas", "lowcost"),
    ("VB", "VIV", "Viva Aerobus", "lowcost"),
    ("Y4", "VOI", "Volaris", "lowcost"),
    ("AK", "AXM", "AirAsia", "lowcost"),
    ("D7", "XAX", "AirAsia X", "lowcost"),
    ("QZ", "AWQ", "Indonesia AirAsia", "lowcost"),
    ("6E", "IGO", "IndiGo", "lowcost"),
    ("G8", "GOW", "GoAir / Go First", "lowcost"),
    ("SG", "SEJ", "SpiceJet", "lowcost"),
    ("JT", "LNI", "Lion Air", "lowcost"),
    ("QG", "CTV", "Citilink", "lowcost"),
    ("TR", "TGW", "Scoot", "lowcost"),
    ("3K", "JSA", "Jetstar Asia", "lowcost"),
    ("JQ", "JST", "Jetstar Airways", "lowcost"),
    ("5J", "CEB", "Cebu Pacific Air", "lowcost"),
    ("PC", "PGT", "Pegasus Airlines", "lowcost"),
    ("FD", "AIQ", "Thai AirAsia", "lowcost"),
    ("VJ", "VJC", "VietJet Air", "lowcost"),
    ("FZ", "FDB", "Flydubai", "lowcost"),
    ("BJ", "LBT", "Nouvelair Tunisia", "lowcost"),
    ("G9", "ABY", "Air Arabia", "lowcost"),
    ("QS", "TVS", "Smartwings", "lowcost"),
    ("HV", "TRA", "Transavia", "lowcost"),
    ("TO", "TVF", "Transavia France", "lowcost"),
    ("E4", "ENT", "Enter Air", "lowcost"),
    ("XY", "KNE", "Flynas", "lowcost"),

    # --- Legacy / mainline -------------------------------------------
    ("AF", "AFR", "Air France", "legacy"),
    ("KL", "KLM", "KLM Royal Dutch Airlines", "legacy"),
    ("LH", "DLH", "Lufthansa", "legacy"),
    ("BA", "BAW", "British Airways", "legacy"),
    ("IB", "IBE", "Iberia", "legacy"),
    ("TP", "TAP", "TAP Air Portugal", "legacy"),
    ("LX", "SWR", "Swiss International Air Lines", "legacy"),
    ("OS", "AUA", "Austrian Airlines", "legacy"),
    ("SN", "BEL", "Brussels Airlines", "legacy"),
    ("SK", "SAS", "SAS Scandinavian Airlines", "legacy"),
    ("AY", "FIN", "Finnair", "legacy"),
    ("EI", "EIN", "Aer Lingus", "legacy"),
    ("AZ", "ITY", "ITA Airways", "legacy"),
    ("TK", "THY", "Turkish Airlines", "legacy"),
    ("EK", "UAE", "Emirates", "legacy"),
    ("EY", "ETD", "Etihad Airways", "legacy"),
    ("QR", "QTR", "Qatar Airways", "legacy"),
    ("SV", "SVA", "Saudia", "legacy"),
    ("SQ", "SIA", "Singapore Airlines", "legacy"),
    ("CX", "CPA", "Cathay Pacific Airways", "legacy"),
    ("JL", "JAL", "Japan Airlines", "legacy"),
    ("NH", "ANA", "All Nippon Airways", "legacy"),
    ("KE", "KAL", "Korean Air", "legacy"),
    ("OZ", "AAR", "Asiana Airlines", "legacy"),
    ("QF", "QFA", "Qantas Airways", "legacy"),
    ("AC", "ACA", "Air Canada", "legacy"),
    ("UA", "UAL", "United Airlines", "legacy"),
    ("AA", "AAL", "American Airlines", "legacy"),
    ("DL", "DAL", "Delta Air Lines", "legacy"),
    ("CA", "CCA", "Air China", "legacy"),
    ("CZ", "CSN", "China Southern Airlines", "legacy"),
    ("MU", "CES", "China Eastern Airlines", "legacy"),
    ("MS", "MSR", "Egypt Air", "legacy"),
    ("AT", "RAM", "Royal Air Maroc", "legacy"),
    ("KQ", "KQA", "Kenya Airways", "legacy"),
    ("ET", "ETH", "Ethiopian Airlines", "legacy"),
    ("AV", "AVA", "Avianca", "legacy"),
    ("LA", "LAN", "LATAM Chile", "legacy"),
    ("JJ", "TAM", "LATAM Brasil", "legacy"),
    ("AM", "AMX", "Aeromexico", "legacy"),
    ("AI", "AIC", "Air India", "legacy"),
    ("UK", "VTI", "Vistara", "legacy"),
    ("SA", "SAA", "South African Airways", "legacy"),
    ("NZ", "ANZ", "Air New Zealand", "legacy"),
    ("VS", "VIR", "Virgin Atlantic Airways", "legacy"),
    ("FI", "ICE", "Icelandair", "legacy"),
    ("LO", "LOT", "LOT Polish Airlines", "legacy"),
    ("OU", "CTN", "Croatia Airlines", "legacy"),
    ("RJ", "RJA", "Royal Jordanian", "legacy"),
    ("KU", "KAC", "Kuwait Airways", "legacy"),
    ("WY", "OMA", "Oman Air", "legacy"),
    ("GF", "GFA", "Gulf Air", "legacy"),
    ("MH", "MAS", "Malaysia Airlines", "legacy"),
    ("PR", "PAL", "Philippine Airlines", "legacy"),
    ("GA", "GIA", "Garuda Indonesia", "legacy"),
    ("TG", "THA", "Thai Airways International", "legacy"),
    ("CI", "CAL", "China Airlines", "legacy"),
    ("BR", "EVA", "EVA Air", "legacy"),
    ("KC", "KZR", "Air Astana", "legacy"),

    # --- Cargo ---------------------------------------------------------
    ("FX", "FDX", "FedEx Express", "cargo"),
    ("5X", "UPS", "United Parcel Service (UPS)", "cargo"),
    ("CV", "CLX", "Cargolux", "cargo"),
    ("RU", "ABW", "AirBridgeCargo", "cargo"),
    ("5Y", "GTI", "Atlas Air", "cargo"),
    ("PO", "PAC", "Polar Air Cargo", "cargo"),
    ("KZ", "NCA", "Nippon Cargo Airlines", "cargo"),
    ("VI", "VDA", "Volga-Dnepr Airlines", "cargo"),
    ("D0", "DHK", "DHL Air", "cargo"),

    # --- Régionales ------------------------------------------------
    ("A5", "HOP", "HOP! (Air France)", "regional"),
    ("OO", "SKW", "SkyWest Airlines", "regional"),
    ("MQ", "EGF", "American Eagle", "regional"),
    ("QK", "JZA", "Jazz Aviation", "regional"),
    ("YV", "ASH", "Mesa Airlines", "regional"),
    ("YW", "ANS", "Air Nostrum", "regional"),
    ("YS", "RAE", "Régional", "regional"),
    ("T7", "TJT", "Twin Jet", "regional"),
    ("XK", "CCM", "Air Corsica", "regional"),
    ("WF", "WIF", "Widerøe", "regional"),
    ("NT", "IBB", "Binter Canarias", "regional"),
    ("RP", "CHQ", "Chautauqua Airlines", "regional"),

    # --- Charter / affrètement --------------------------------------
    ("SS", "CRL", "Corsair International", "charter"),
    ("SE", "XLF", "XL Airways France", "charter"),
    ("DE", "CFG", "Condor", "charter"),
    ("NO", "NOS", "Neos", "charter"),
]

# structures de recherche rapide (remplies plus bas, après le
# chargement éventuel des extensions CSV)
AIRLINE_BY_IATA = {}
AIRLINE_BY_ICAO = {}


def _register_airline(iata, icao, name, category):
    rec = {
        "iata": (iata or "").upper(),
        "icao": (icao or "").upper(),
        "name": name,
        "category": category if category in
        ("lowcost", "legacy", "cargo", "regional", "charter", "other")
        else "other",
    }
    if rec["iata"]:
        AIRLINE_BY_IATA[rec["iata"]] = rec
    if rec["icao"]:
        AIRLINE_BY_ICAO[rec["icao"]] = rec


for _iata, _icao, _name, _cat in AIRLINES_RAW:
    _register_airline(_iata, _icao, _name, _cat)


# =====================================================================
#  2. BASE DE DONNEES "TYPES D'AVIONS" (code ICAO -> catégorie)
#     catégorie parmi : ga / narrow / wide / super
# =====================================================================

AIRCRAFT_CATEGORIES_RAW = {
    "ga": [
        "C172", "C152", "C150", "C182", "C206", "C210",
        "P28A", "P28R", "P32R", "PA28", "PA34", "PA44",
        "DA40", "DA42", "DA62", "SR20", "SR22", "SR2T",
        "BE33", "BE35", "BE36", "BE58", "M20P", "M20T",
        "RV10", "RV7", "GLST", "AA5", "DR40", "DR22",
        "TB10", "TB20", "TB21", "C210",
    ],
    "narrow": [
        "A319", "A320", "A321", "A20N", "A21N",
        "B737", "B738", "B739", "B37M", "B38M", "B39M", "B3XM",
        "E170", "E175", "E190", "E195", "E290", "E295",
        "CRJ2", "CRJ7", "CRJ9", "CRJX",
        "AT43", "AT45", "AT72", "AT76", "DH8D", "B190",
        "MD82", "MD83", "MD88", "MD90",
    ],
    "wide": [
        "A332", "A333", "A338", "A339",
        "A342", "A343", "A345", "A346",
        "A359", "A35K",
        "B762", "B763", "B764",
        "B772", "B773", "B77L", "B77W",
        "B788", "B789", "B78X",
        "MD11",
    ],
    "super": [
        "A388", "B742", "B743", "B744", "B748",
    ],
}

AIRCRAFT_CODE_TO_CATEGORY = {}
for _cat, _codes in AIRCRAFT_CATEGORIES_RAW.items():
    for _code in _codes:
        AIRCRAFT_CODE_TO_CATEGORY[_code.upper()] = _cat


# =====================================================================
#  3. EXTENSIBILITE : chargement de fichiers CSV optionnels
#     - airlines_extra.csv  : colonnes  iata,icao,nom,categorie
#     - aircraft_extra.csv  : colonnes  code_icao,categorie
#     Ces fichiers, s'ils existent à côté du script, permettent de
#     compléter les deux bases ci-dessus sans toucher au code.
# =====================================================================

def _script_dir():
    return os.path.dirname(os.path.abspath(__file__))


def load_extra_airlines():
    path = os.path.join(_script_dir(), "airlines_extra.csv")
    if not os.path.isfile(path):
        return 0
    count = 0
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0].strip().lower() in ("iata", "#"):
                    continue
                row = row + [""] * (4 - len(row))
                iata, icao, name, cat = [c.strip() for c in row[:4]]
                if not (iata or icao):
                    continue
                _register_airline(iata, icao, name or (iata or icao), cat.lower())
                count += 1
    except Exception as exc:  # pragma: no cover - robustesse de chargement
        print(f"[avertissement] airlines_extra.csv ignoré : {exc}")
    return count


def load_extra_aircraft():
    path = os.path.join(_script_dir(), "aircraft_extra.csv")
    if not os.path.isfile(path):
        return 0
    count = 0
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0].strip().lower() in ("code_icao", "#"):
                    continue
                row = row + [""] * (2 - len(row))
                code, cat = [c.strip() for c in row[:2]]
                cat = cat.lower()
                if not code or cat not in ("ga", "narrow", "wide", "super"):
                    continue
                AIRCRAFT_CODE_TO_CATEGORY[code.upper()] = cat
                AIRCRAFT_CATEGORIES_RAW.setdefault(cat, []).append(code.upper())
                count += 1
    except Exception as exc:  # pragma: no cover
        print(f"[avertissement] aircraft_extra.csv ignoré : {exc}")
    return count


_nb_extra_airlines = load_extra_airlines()
_nb_extra_aircraft = load_extra_aircraft()
if _nb_extra_airlines:
    print(f"[info] {_nb_extra_airlines} compagnie(s) supplémentaire(s) chargée(s) depuis airlines_extra.csv")
if _nb_extra_aircraft:
    print(f"[info] {_nb_extra_aircraft} type(s) d'avion supplémentaire(s) chargé(s) depuis aircraft_extra.csv")


# =====================================================================
#  4. LOGIQUE METIER
# =====================================================================

CYCLE_RATE_BY_ACTIVITY = {
    "lowcost": 1200,
    "legacy": 750,
    "cargo": 650,
    "regional": 1500,
    "charter": 500,
    "other": 800,
}

GA_INTENSITY_RATE = {
    "intensive": 300,
    "moyenne": 120,
    "faible": 40,
}

MAINTENANCE_DEFAULT_BY_ACTIVITY = {
    "lowcost": "bonne",
    "legacy": "excellente",
    "cargo": "normale",
    "regional": "normale",
    "charter": "normale",
    "other": "normale",
    "ga": "normale",
}

ALPHA_BY_CATEGORY = {"ga": 1.2, "narrow": 2.0, "wide": 1.7, "super": 1.6}
MAINTENANCE_MULTIPLIER = {"excellente": 0.7, "bonne": 0.85, "normale": 1.0, "mauvaise": 1.3}


def find_airline(code):
    """Recherche une compagnie par code IATA ou ICAO (insensible à la casse)."""
    code = (code or "").strip().upper()
    if not code:
        return None
    return AIRLINE_BY_ICAO.get(code) or AIRLINE_BY_IATA.get(code)


def detect_aircraft_category(type_code):
    """Retourne la catégorie ('ga'/'narrow'/'wide'/'super') d'un code ICAO avion, ou None."""
    return AIRCRAFT_CODE_TO_CATEGORY.get((type_code or "").strip().upper())


def estimate_cycle_rate(activity_code, ga_intensity_code=None):
    if activity_code == "ga":
        return GA_INTENSITY_RATE.get(ga_intensity_code, GA_INTENSITY_RATE["moyenne"])
    return CYCLE_RATE_BY_ACTIVITY.get(activity_code, CYCLE_RATE_BY_ACTIVITY["other"])


def compute_human_age(age_years, cycles, category_code, maintenance_code):
    alpha = ALPHA_BY_CATEGORY.get(category_code, 2.0)
    m = MAINTENANCE_MULTIPLIER.get(maintenance_code, 1.0)
    return round(alpha * (age_years ** 0.9) * (1 + (cycles / 60000) * m), 1)


def verdict_for_human_age(human_age):
    if human_age < 12:
        return "Avion encore jeune, en pleine forme", "#1a7f37"
    if human_age < 30:
        return "Avion dans la force de l'âge", "#946200"
    if human_age < 55:
        return "Avion senior, surveillance accrue recommandée", "#b35c00"
    if human_age < 80:
        return "Avion très âgé, proche de la retraite", "#c0392b"
    return "Avion centenaire… bon pour le musée ! ✈️🏛️", "#7a0000"


# =====================================================================
#  5. INTERFACE GRAPHIQUE (Tkinter / ttk) — tout dans une seule fenêtre
# =====================================================================

ACTIVITY_OPTIONS = [
    ("Compagnie low-cost", "lowcost"),
    ("Compagnie legacy / mainline", "legacy"),
    ("Compagnie cargo", "cargo"),
    ("Compagnie régionale", "regional"),
    ("Vol charter / affrètement", "charter"),
    ("Aviation générale (GA)", "ga"),
    ("Autre / inconnu", "other"),
]

MAINTENANCE_OPTIONS = [
    ("Excellente", "excellente"),
    ("Bonne", "bonne"),
    ("Normale", "normale"),
    ("Mauvaise", "mauvaise"),
]

GA_INTENSITY_OPTIONS = [
    ("Intensive (école de pilotage, club très actif)", "intensive"),
    ("Moyenne (usage régulier de loisir)", "moyenne"),
    ("Faible (usage occasionnel)", "faible"),
]

CATEGORY_OPTIONS = [
    ("Aviation générale (GA)", "ga"),
    ("Monocouloir (narrow-body)", "narrow"),
    ("Long-courrier (wide-body)", "wide"),
    ("Très gros porteur (A380, 747...)", "super"),
]


def _build_maps(options):
    label_to_code = {label: code for label, code in options}
    code_to_label = {code: label for label, code in options}
    return label_to_code, code_to_label


ACT_LABEL2CODE, ACT_CODE2LABEL = _build_maps(ACTIVITY_OPTIONS)
MAINT_LABEL2CODE, MAINT_CODE2LABEL = _build_maps(MAINTENANCE_OPTIONS)
GA_LABEL2CODE, GA_CODE2LABEL = _build_maps(GA_INTENSITY_OPTIONS)
CAT_LABEL2CODE, CAT_CODE2LABEL = _build_maps(CATEGORY_OPTIONS)

BG = "#f4f6fa"
CARD_BG = "#ffffff"
ACCENT = "#1f6feb"
TEXT_MUTED = "#5b6472"


class App:
    def __init__(self, root):
        self.root = root
        root.title("✈️ Age Avion → Age Humain")
        root.configure(bg=BG)
        root.geometry("760x900")
        root.minsize(680, 760)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=BG)
        style.configure("Card.TLabelframe", background=CARD_BG, borderwidth=1, relief="solid")
        style.configure("Card.TLabelframe.Label", background=CARD_BG, foreground=ACCENT,
                         font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background=CARD_BG, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=CARD_BG, foreground=TEXT_MUTED, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=BG, foreground="#111827",
                         font=("Segoe UI", 18, "bold"))
        style.configure("SubHeader.TLabel", background=BG, foreground=TEXT_MUTED,
                         font=("Segoe UI", 10))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TCheckbutton", background=CARD_BG)

        # ---- variables --------------------------------------------------
        self.registration_var = tk.StringVar()
        self.airline_code_var = tk.StringVar()
        self.airline_status_var = tk.StringVar(value="Aucune compagnie recherchée pour l'instant.")
        self.aircraft_code_var = tk.StringVar()
        self.category_label_var = tk.StringVar(value=CAT_CODE2LABEL["narrow"])
        self.activity_label_var = tk.StringVar(value=ACT_CODE2LABEL["other"])
        self.maintenance_label_var = tk.StringVar(value=MAINT_CODE2LABEL["normale"])
        self.ga_intensity_label_var = tk.StringVar(value=GA_CODE2LABEL["moyenne"])
        self.age_var = tk.StringVar()
        self.custom_cycles_enabled = tk.BooleanVar(value=False)
        self.custom_cycles_var = tk.StringVar()
        self.error_var = tk.StringVar(value="")
        self.result_title_var = tk.StringVar(value="—")
        self.result_details_var = tk.StringVar(value="Renseignez les champs ci-dessus puis cliquez sur Calculer.")
        self.export_status_var = tk.StringVar(value="")

        self._build_layout()
        self._on_activity_change()

    # ------------------------------------------------------------------
    #  Construction de l'interface
    # ------------------------------------------------------------------
    def _build_layout(self):
        header = ttk.Frame(self.root, style="TFrame")
        header.pack(fill="x", padx=20, pady=(18, 6))
        ttk.Label(header, text="✈️ Age Avion → Age Humain", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Estimez l'âge « humain » d'un avion à partir de son type et de son exploitant.",
            style="SubHeader.TLabel",
        ).pack(anchor="w")

        container = ttk.Frame(self.root, style="TFrame")
        container.pack(fill="both", expand=True, padx=20, pady=6)

        self._build_airline_section(container)
        self._build_aircraft_section(container)
        self._build_operation_section(container)
        self._build_age_section(container)
        self._build_actions(container)
        self._build_result_section(container)
        self._build_history_section(container)

    def _card(self, parent, title):
        frame = ttk.LabelFrame(parent, text=title, style="Card.TLabelframe", padding=12)
        frame.pack(fill="x", pady=6)
        return frame

    def _build_airline_section(self, parent):
        card = self._card(parent, "1. Compagnie aérienne (optionnel)")
        row = ttk.Frame(card, style="TFrame")
        row.configure(style="TFrame")
        row.pack(fill="x")
        row.pack_configure()
        row.pack_forget()  # (frame remplacé ci-dessous par un usage direct de grid)

        card.grid_columnconfigure(1, weight=1)
        ttk.Label(card, text="Code IATA ou ICAO :", background=CARD_BG).grid(row=0, column=0, sticky="w", pady=3)
        entry = ttk.Entry(card, textvariable=self.airline_code_var, width=10)
        entry.grid(row=0, column=1, sticky="w", pady=3)
        entry.bind("<Return>", lambda e: self.on_airline_lookup())
        ttk.Button(card, text="Rechercher", command=self.on_airline_lookup).grid(row=0, column=2, sticky="w", padx=(8, 0))

        ttk.Label(card, textvariable=self.airline_status_var, style="Muted.TLabel", wraplength=620,
                  justify="left").grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))

        ttk.Label(card, text="Immatriculation (facultatif, pour vos notes) :", background=CARD_BG).grid(
            row=2, column=0, sticky="w", pady=(10, 3))
        ttk.Entry(card, textvariable=self.registration_var, width=12).grid(row=2, column=1, sticky="w", pady=(10, 3))

    def _build_aircraft_section(self, parent):
        card = self._card(parent, "2. Avion")
        card.grid_columnconfigure(1, weight=1)

        ttk.Label(card, text="Code type ICAO :", background=CARD_BG).grid(row=0, column=0, sticky="w", pady=3)
        codes = sorted(AIRCRAFT_CODE_TO_CATEGORY.keys())
        combo = ttk.Combobox(card, textvariable=self.aircraft_code_var, values=codes, width=12)
        combo.grid(row=0, column=1, sticky="w", pady=3)
        combo.bind("<<ComboboxSelected>>", lambda e: self.on_aircraft_type_change())
        combo.bind("<FocusOut>", lambda e: self.on_aircraft_type_change())
        combo.bind("<Return>", lambda e: self.on_aircraft_type_change())

        ttk.Label(card, text="Catégorie :", background=CARD_BG).grid(row=1, column=0, sticky="w", pady=3)
        cat_combo = ttk.Combobox(card, textvariable=self.category_label_var,
                                  values=[label for label, _ in CATEGORY_OPTIONS],
                                  state="readonly", width=32)
        cat_combo.grid(row=1, column=1, sticky="w", pady=3)

        ttk.Label(card, text="(la catégorie est proposée automatiquement à partir du code ICAO,\n"
                              "mais vous pouvez toujours la changer vous-même)",
                  style="Muted.TLabel", justify="left").grid(row=2, column=0, columnspan=2, sticky="w")

    def _build_operation_section(self, parent):
        card = self._card(parent, "3. Type d'activité et maintenance")
        card.grid_columnconfigure(1, weight=1)

        ttk.Label(card, text="Type d'activité :", background=CARD_BG).grid(row=0, column=0, sticky="w", pady=3)
        act_combo = ttk.Combobox(card, textvariable=self.activity_label_var,
                                  values=[label for label, _ in ACTIVITY_OPTIONS],
                                  state="readonly", width=32)
        act_combo.grid(row=0, column=1, sticky="w", pady=3)
        act_combo.bind("<<ComboboxSelected>>", lambda e: self._on_activity_change())

        # sous-cadre GA, affiché seulement si activité == GA
        self.ga_frame = ttk.Frame(card, style="TFrame")
        self.ga_frame.configure(style="TFrame")
        self.ga_frame.grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 4))
        ttk.Label(self.ga_frame, text="Intensité d'utilisation (GA) :", background=CARD_BG).grid(
            row=0, column=0, sticky="w")
        ga_combo = ttk.Combobox(self.ga_frame, textvariable=self.ga_intensity_label_var,
                                 values=[label for label, _ in GA_INTENSITY_OPTIONS],
                                 state="readonly", width=40)
        ga_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))

        ttk.Label(card, text="Qualité de maintenance :", background=CARD_BG).grid(row=2, column=0, sticky="w", pady=3)
        maint_combo = ttk.Combobox(card, textvariable=self.maintenance_label_var,
                                    values=[label for label, _ in MAINTENANCE_OPTIONS],
                                    state="readonly", width=20)
        maint_combo.grid(row=2, column=1, sticky="w", pady=3)

        ttk.Checkbutton(card, text="Utiliser un nombre de cycles personnalisé",
                         variable=self.custom_cycles_enabled,
                         command=self._on_custom_cycles_toggle).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 2))
        self.cycles_entry = ttk.Entry(card, textvariable=self.custom_cycles_var, width=12, state="disabled")
        self.cycles_entry.grid(row=4, column=0, sticky="w")
        ttk.Label(card, text="(nombre total de cycles décollage/atterrissage connu de l'avion)",
                  style="Muted.TLabel").grid(row=4, column=1, sticky="w")

    def _build_age_section(self, parent):
        card = self._card(parent, "4. Âge de l'avion")
        ttk.Label(card, text="Âge (en années) :", background=CARD_BG).grid(row=0, column=0, sticky="w")
        ttk.Entry(card, textvariable=self.age_var, width=10).grid(row=0, column=1, sticky="w", padx=(8, 0))

    def _build_actions(self, parent):
        row = ttk.Frame(parent, style="TFrame")
        row.pack(fill="x", pady=(4, 4))
        ttk.Button(row, text="Calculer", style="Accent.TButton", command=self.on_calculate).pack(side="left")
        ttk.Button(row, text="Réinitialiser", command=self.on_reset).pack(side="left", padx=8)
        ttk.Button(row, text="Exporter le résultat", command=self.on_export).pack(side="left")
        ttk.Label(parent, textvariable=self.error_var, foreground="#c0392b", background=BG,
                  wraplength=680, justify="left").pack(fill="x")
        ttk.Label(parent, textvariable=self.export_status_var, foreground="#1a7f37", background=BG,
                  wraplength=680, justify="left").pack(fill="x")

    def _build_result_section(self, parent):
        card = self._card(parent, "Résultat")
        self.result_title_label = tk.Label(card, textvariable=self.result_title_var, bg=CARD_BG,
                                            font=("Segoe UI", 22, "bold"), fg="#111827")
        self.result_title_label.pack(anchor="w")
        ttk.Label(card, textvariable=self.result_details_var, style="Muted.TLabel", justify="left",
                  wraplength=680).pack(anchor="w", pady=(4, 0))

    def _build_history_section(self, parent):
        card = self._card(parent, "Historique de la session")
        columns = ("heure", "immat", "compagnie", "avion", "age", "age_humain")
        self.tree = ttk.Treeview(card, columns=columns, show="headings", height=6)
        headers = {
            "heure": "Heure", "immat": "Immat.", "compagnie": "Compagnie",
            "avion": "Type avion", "age": "Âge (ans)", "age_humain": "Âge humain",
        }
        widths = {"heure": 70, "immat": 70, "compagnie": 140, "avion": 90, "age": 70, "age_humain": 90}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.pack(fill="x", pady=(0, 6))
        ttk.Button(card, text="Effacer l'historique", command=self.on_clear_history).pack(anchor="e")

    # ------------------------------------------------------------------
    #  Callbacks
    # ------------------------------------------------------------------
    def on_airline_lookup(self):
        code = self.airline_code_var.get()
        airline = find_airline(code)
        if not airline:
            self.airline_status_var.set(
                f"Compagnie « {code.strip().upper()} » non trouvée dans la base embarquée. "
                f"Vous pouvez continuer entièrement en mode manuel ci-dessous, ou compléter "
                f"« airlines_extra.csv » pour l'ajouter."
            )
            return
        self.airline_status_var.set(
            f"Trouvé : {airline['name']}  (IATA {airline['iata'] or '—'} / ICAO {airline['icao'] or '—'}) "
            f"— catégorie : {ACT_CODE2LABEL.get(airline['category'], airline['category'])}."
        )
        self.activity_label_var.set(ACT_CODE2LABEL.get(airline["category"], ACT_CODE2LABEL["other"]))
        self._on_activity_change()
        default_maint = MAINTENANCE_DEFAULT_BY_ACTIVITY.get(airline["category"], "normale")
        self.maintenance_label_var.set(MAINT_CODE2LABEL[default_maint])

    def on_aircraft_type_change(self):
        code = self.aircraft_code_var.get()
        category = detect_aircraft_category(code)
        if category:
            self.category_label_var.set(CAT_CODE2LABEL[category])
        elif code.strip():
            self.error_var.set(
                f"Type d'avion « {code.strip().upper()} » non reconnu : choisissez la catégorie "
                f"manuellement ci-dessus (ou complétez « aircraft_extra.csv »)."
            )

    def _on_activity_change(self):
        activity_code = ACT_LABEL2CODE.get(self.activity_label_var.get(), "other")
        if activity_code == "ga":
            self.ga_frame.grid()
        else:
            self.ga_frame.grid_remove()

    def _on_custom_cycles_toggle(self):
        state = "normal" if self.custom_cycles_enabled.get() else "disabled"
        self.cycles_entry.configure(state=state)

    def on_reset(self):
        self.registration_var.set("")
        self.airline_code_var.set("")
        self.airline_status_var.set("Aucune compagnie recherchée pour l'instant.")
        self.aircraft_code_var.set("")
        self.category_label_var.set(CAT_CODE2LABEL["narrow"])
        self.activity_label_var.set(ACT_CODE2LABEL["other"])
        self.maintenance_label_var.set(MAINT_CODE2LABEL["normale"])
        self.ga_intensity_label_var.set(GA_CODE2LABEL["moyenne"])
        self.age_var.set("")
        self.custom_cycles_enabled.set(False)
        self.custom_cycles_var.set("")
        self._on_custom_cycles_toggle()
        self._on_activity_change()
        self.error_var.set("")
        self.export_status_var.set("")
        self.result_title_var.set("—")
        self.result_details_var.set("Renseignez les champs ci-dessus puis cliquez sur Calculer.")

    def on_calculate(self):
        self.error_var.set("")
        self.export_status_var.set("")

        age_text = self.age_var.get().strip().replace(",", ".")
        try:
            age = float(age_text)
            if age <= 0:
                raise ValueError
        except ValueError:
            self.error_var.set("Merci de saisir un âge d'avion valide (nombre positif, en années).")
            return

        category_code = CAT_LABEL2CODE.get(self.category_label_var.get(), "narrow")
        activity_code = ACT_LABEL2CODE.get(self.activity_label_var.get(), "other")
        maintenance_code = MAINT_LABEL2CODE.get(self.maintenance_label_var.get(), "normale")
        ga_intensity_code = GA_LABEL2CODE.get(self.ga_intensity_label_var.get(), "moyenne")

        if self.custom_cycles_enabled.get():
            cycles_text = self.custom_cycles_var.get().strip()
            try:
                cycles = int(float(cycles_text))
                if cycles < 0:
                    raise ValueError
            except ValueError:
                self.error_var.set("Le nombre de cycles personnalisé doit être un entier positif.")
                return
        else:
            rate = estimate_cycle_rate(activity_code, ga_intensity_code)
            cycles = int(age * rate)

        human_age = compute_human_age(age, cycles, category_code, maintenance_code)
        verdict_text, verdict_color = verdict_for_human_age(human_age)

        self.result_title_var.set(f"{human_age} ans (âge humain)")
        self.result_title_label.configure(fg=verdict_color)

        airline = find_airline(self.airline_code_var.get())
        airline_name = airline["name"] if airline else "— (mode manuel)"

        details = (
            f"{verdict_text}\n"
            f"Compagnie : {airline_name}   |   Catégorie avion : {self.category_label_var.get()}\n"
            f"Type d'activité : {self.activity_label_var.get()}"
        )
        if activity_code == "ga":
            details += f" — {self.ga_intensity_label_var.get()}"
        details += (
            f"\nMaintenance : {self.maintenance_label_var.get()}   |   "
            f"Cycles estimés : {cycles}   |   Âge réel : {age} ans"
        )
        self.result_details_var.set(details)

        self._last_result = {
            "heure": time.strftime("%H:%M:%S"),
            "immat": self.registration_var.get().strip().upper() or "—",
            "compagnie": airline_name,
            "avion": self.aircraft_code_var.get().strip().upper() or "—",
            "age": age,
            "age_humain": human_age,
            "details": details,
        }
        self.tree.insert("", "end", values=(
            self._last_result["heure"], self._last_result["immat"], self._last_result["compagnie"],
            self._last_result["avion"], self._last_result["age"], self._last_result["age_humain"],
        ))

    def on_clear_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def on_export(self):
        if not hasattr(self, "_last_result"):
            self.error_var.set("Aucun résultat à exporter : lancez d'abord un calcul.")
            return
        path = os.path.join(_script_dir(), "resultats_age_avion.txt")
        try:
            with open(path, "a", encoding="utf-8") as f:
                r = self._last_result
                f.write(f"[{r['heure']}] Immat={r['immat']} Avion={r['avion']} "
                        f"Compagnie={r['compagnie']} Age={r['age']} -> AgeHumain={r['age_humain']}\n")
                f.write(f"    {r['details'].replace(chr(10), ' | ')}\n\n")
            self.export_status_var.set(f"Résultat ajouté à : {path}")
        except OSError as exc:
            self.error_var.set(f"Impossible d'écrire le fichier d'export : {exc}")


# =====================================================================
#  6. NOTE SUR LA BASE OFFICIELLE ICAO DOC 8643
# =====================================================================
# La base complète et officielle des désignateurs de type d'aéronef
# (ICAO Doc 8643) n'est pas librement téléchargeable : elle est
# consultable uniquement via un moteur de recherche en ligne restreint
# (icao.int) ou vendue sous forme de document PDF payant, sans export
# CSV public. Il n'a donc pas été possible d'en extraire "tous les
# codes" automatiquement. La liste embarquée ci-dessus couvre les
# avions les plus courants (aviation générale, monocouloirs,
# long-courriers, très gros porteurs) et peut être complétée à tout
# moment via le fichier "aircraft_extra.csv" (voir section
# EXTENSIBILITE en haut de ce fichier), par exemple en copiant les
# codes trouvés un par un sur le site de recherche de l'ICAO.


# =====================================================================
#  MAIN
# =====================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
