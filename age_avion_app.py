#!/usr/bin/env python3

import os
import json
import time
import requests
import tkinter as tk
from tkinter import messagebox, simpledialog

CACHE_FILE = "cache_avions.json"

# ================= API =================
def get_aircraft_data_from_avio(registration):
    try:
        url = f"https://avioadsb.org/v1/reg/{registration}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        j = r.json()
        if not j.get("ac"):
            return None
        ac = j["ac"][0]
        return {
            "type": ac.get("t") or "UNKNOWN",
            "callsign": ac.get("flight") or ""
        }
    except:
        return None

# ================= LOGIQUE =================
def detect_category_from_type(t):
    t = (t or "").upper()

    if any(x in t for x in ["C172","PA28","DR40","SR22"]):
        return "ga"

    if any(x in t for x in ["A320","A321","A319","B737","E190","CRJ"]):
        return "narrow"

    if any(x in t for x in ["A330","A350","B777","B787"]):
        return "wide"

    if any(x in t for x in ["A380","B747"]):
        return "super"

    return "narrow"

def estimate_cycles_by_airline(age, category, airline):
    if not airline:
        return int(age * 800)

    airline = airline.upper()

    low_cost = {"FR","U2","W6"}
    legacy = {"AF","LH","BA","KL"}
    cargo = {"FX","5X"}

    if airline in low_cost:
        return int(age * 1200)
    elif airline in legacy:
        return int(age * 900)
    elif airline in cargo:
        return int(age * 800)
    else:
        return int(age * 850)

def estimate_maintenance(airline):
    if not airline:
        return "normale"

    airline = airline.upper()

    good = {"AF","LH","BA","KL"}

    if airline in good:
        return "bonne"
    return "normale"

def calcul_age_humain(age, cycles, category, maintenance):
    alpha = {"ga":1.2,"narrow":2,"wide":1.7,"super":1.6}.get(category,2)
    m = {"excellente":0.7,"bonne":0.85,"normale":1,"mauvaise":1.3}.get(maintenance,1)
    return round(alpha * (age ** 0.9) * (1 + (cycles/60000)*m),1)

def detect_airline_from_callsign(cs):
    if not cs:
        return None
    return cs[:2].upper()

# ================= APP =================
class App:
    def __init__(self, root):
        self.root = root
        root.title("Age humain avion")

        tk.Label(root, text="Immatriculation").pack()
        self.reg = tk.Entry(root)
        self.reg.pack()

        tk.Button(root, text="Lookup", command=self.lookup).pack()
        tk.Button(root, text="Mode manuel", command=self.manual).pack()

        self.type = tk.StringVar(value="N/A")
        self.airline = tk.StringVar(value="N/A")
        self.cat = tk.StringVar(value="N/A")

        tk.Label(root, textvariable=self.type).pack()
        tk.Label(root, textvariable=self.airline).pack()
        tk.Label(root, textvariable=self.cat).pack()

        tk.Label(root, text="Age avion").pack()
        self.age = tk.Entry(root)
        self.age.pack()

        tk.Button(root, text="Calculer", command=self.calc).pack()

        self.result = tk.StringVar(value="")
        tk.Label(root, textvariable=self.result).pack()

    # ===== LOOKUP AVEC FALLBACK =====
    def lookup(self):
        reg = self.reg.get().strip().upper()
        if not reg:
            messagebox.showwarning("Erreur", "Entre une immatriculation")
            return

        data = get_aircraft_data_from_avio(reg)

        # 🔥 FALLBACK
        if not data:
            if messagebox.askyesno("Pas trouvé", "Mode manuel ?"):
                self.manual()
            return

        atype = data["type"]
        callsign = data["callsign"]

        self.type.set(atype)

        airline = detect_airline_from_callsign(callsign)
        self.airline.set(airline or "N/A")

        cat = detect_category_from_type(atype)
        self.cat.set(cat)

    # ===== MODE MANUEL =====
    def manual(self):
        t = simpledialog.askstring("Type avion", "Ex: A320")
        a = simpledialog.askstring("Compagnie", "Ex: AF")

        self.type.set(t or "UNKNOWN")
        self.airline.set(a or "N/A")
        self.cat.set(detect_category_from_type(t))

    # ===== CALCUL =====
    def calc(self):
        try:
            age = float(self.age.get())
        except:
            messagebox.showerror("Erreur", "Age invalide")
            return

        cat = self.cat.get()
        airline = self.airline.get()

        cycles = estimate_cycles_by_airline(age, cat, airline)
        maintenance = estimate_maintenance(airline)

        human = calcul_age_humain(age, cycles, cat, maintenance)

        self.result.set(
            f"Type: {self.type.get()}\n"
            f"Compagnie: {airline}\n"
            f"Catégorie: {cat}\n"
            f"Cycles: {cycles}\n"
            f"Maintenance: {maintenance}\n\n"
            f"=> Age humain: {human}"
        )

# ================= MAIN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
