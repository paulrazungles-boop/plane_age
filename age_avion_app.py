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
    if "A3" in t or "B77" in t or "787" in t:
        return "wide"
    if "747" in t or "A380" in t:
        return "super"
    if "C" in t or "PIPER" in t:
        return "ga"
    return "narrow"

def calcul_age_humain(age, cycles, cat):
    alpha = {"ga":1.2, "narrow":2, "wide":1.7, "super":1.6}.get(cat,2)
    return round(alpha * (age ** 0.9) * (1 + cycles/50000),1)

# ================= APP =================
class App:
    def __init__(self, root):
        self.root = root
        root.title("Age avion")

        tk.Label(root, text="Immatriculation").pack()
        self.reg = tk.Entry(root)
        self.reg.pack()

        tk.Button(root, text="Lookup", command=self.lookup).pack()
        tk.Button(root, text="Mode manuel", command=self.manual).pack()

        self.type = tk.StringVar(value="N/A")
        self.cat = tk.StringVar(value="N/A")

        tk.Label(root, textvariable=self.type).pack()
        tk.Label(root, textvariable=self.cat).pack()

        tk.Label(root, text="Age avion").pack()
        self.age = tk.Entry(root)
        self.age.pack()

        tk.Button(root, text="Calculer", command=self.calc).pack()

        self.result = tk.StringVar(value="")
        tk.Label(root, textvariable=self.result).pack()

    def lookup(self):
        reg = self.reg.get()
        data = get_aircraft_data_from_avio(reg)

        if not data:
            if messagebox.askyesno("Erreur", "Pas trouvé. Mode manuel ?"):
                self.manual()
            return

        self.type.set(data["type"])
        cat = detect_category_from_type(data["type"])
        self.cat.set(cat)

    def manual(self):
        t = simpledialog.askstring("Type avion", "Ex: A320")
        self.type.set(t or "UNKNOWN")
        self.cat.set(detect_category_from_type(t))

    def calc(self):
        try:
            age = float(self.age.get())
        except:
            messagebox.showerror("Erreur", "Age invalide")
            return

        cat = self.cat.get()
        cycles = age * 1000

        res = calcul_age_humain(age, cycles, cat)
        self.result.set(f"Age humain: {res}")

# ================= MAIN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()