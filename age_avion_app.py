#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
  AGE AVION -> AGE HUMAIN
=====================================================================
Application de bureau (Tkinter) qui estime l'"âge humain" d'un avion
à partir de :
    - son âge réel (années)
    - sa catégorie (GA, planeur, ULM, hélicoptère, jet d'affaires,
      turbopropulseur régional, jet régional, monocouloir,
      long-courrier, très gros porteur, cargo lourd, voltige,
      warbird/collection... + catégories que VOUS créez vous-même)
    - son exploitant (compagnie), déduit automatiquement du code
      IATA ou ICAO -> propose le "type d'activité" (low-cost, legacy,
      cargo, régionale, charter...) et la "qualité de maintenance"
      par défaut. Vous pouvez aussi créer vos propres compagnies.
    - pour les catégories "club/privé" (GA, planeur, ULM, voltige,
      warbird...) : une intensité d'utilisation (intensive / moyenne
      / faible) remplace la notion de compagnie.

TOUT reste modifiable manuellement, à tout moment, aucun champ n'est
verrouillé (sauf pendant le mode "planeur forcé", voir plus bas).

CHANGEMENTS DE CETTE VERSION
------------------------------------------------
- Beaucoup plus de catégories d'avions embarquées (voir
  CATEGORY_DEFINITIONS), chacune avec son propre coefficient de
  vieillissement.
- Case à cocher "C'est un planeur" : force la catégorie "Planeur"
  sans avoir à connaître/saisir un code ICAO.
- Nouvelle carte "Créer une catégorie personnalisée" : donnez un nom
  et un coefficient de vieillissement (et, si c'est une catégorie de
  type club/privé, des taux d'intensité) ; la catégorie est ajoutée à
  la liste déroulante et sauvegardée dans "categories_extra.csv" pour
  être retrouvée au prochain lancement.
- Nouvelle carte "Créer une compagnie personnalisée" : ajoutez une
  compagnie (codes IATA/ICAO, nom, type d'activité) directement dans
  l'interface ; elle est utilisable immédiatement et sauvegardée dans
  "airlines_extra.csv".
- Interface mise dans un cadre défilant (la fenêtre a grandi avec
  toutes ces nouvelles options).

EXTENSIBILITE PAR FICHIERS (en plus de la création via l'interface)
------------------------------------------------
    - airlines_extra.csv    : iata,icao,nom,categorie
    - aircraft_extra.csv    : code_icao,categorie
    - categories_extra.csv  : code,label,alpha,uses_intensity,
                               rate_intensive,rate_moyenne,rate_faible
=====================================================================
"""

import os
import re
import csv
import time
import unicodedata
import tkinter as tk
from tkinter import ttk

# =====================================================================
#  0. OUTILS GENERAUX
# =====================================================================

def _script_dir():
    return os.path.dirname(os.path.abspath(__file__))


def slugify(text, existing_keys=()):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    if not text:
        text = f"cat_{int(time.time())}"
    base = text
    i = 2
    while text in existing_keys:
        text = f"{base}_{i}"
        i += 1
    return text


# =====================================================================
#  1. BASE DE DONNEES "COMPAGNIES AERIENNES"
#     (code IATA, code ICAO, nom, catégorie d'activité)
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

AIRLINE_BY_IATA = {}
AIRLINE_BY_ICAO = {}
ACTIVITY_CODES = ("lowcost", "legacy", "cargo", "regional", "charter", "other")


def _register_airline(iata, icao, name, category):
    rec = {
        "iata": (iata or "").upper(),
        "icao": (icao or "").upper(),
        "name": name or (iata or icao),
        "category": category if category in ACTIVITY_CODES else "other",
    }
    if rec["iata"]:
        AIRLINE_BY_IATA[rec["iata"]] = rec
    if rec["icao"]:
        AIRLINE_BY_ICAO[rec["icao"]] = rec
    return rec


for _iata, _icao, _name, _cat in AIRLINES_RAW:
    _register_airline(_iata, _icao, _name, _cat)


def append_airline_to_csv(iata, icao, name, category):
    path = os.path.join(_script_dir(), "airlines_extra.csv")
    is_new = not os.path.isfile(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["iata", "icao", "nom", "categorie"])
        writer.writerow([iata, icao, name, category])


# =====================================================================
#  2. CATEGORIES D'AVIONS
#     Chaque catégorie a : un libellé, un coefficient de vieillissement
#     "alpha" (plus il est élevé, plus l'avion "vieillit vite" à âge
#     égal), et éventuellement un mode "club/privé" avec ses propres
#     taux d'intensité (au lieu d'une compagnie).
# =====================================================================

CATEGORY_DEFINITIONS = {
    "ga": {
        "label": "Aviation générale (avion léger à pistons)",
        "alpha": 1.2,
        "uses_intensity": True,
        "intensity_rates": {"intensive": 300, "moyenne": 120, "faible": 40},
        "builtin": True,
    },
    "ga_turbo": {
        "label": "Aviation générale / affaires turbopropulsée (TBM, PC-12, King Air...)",
        "alpha": 1.4,
        "uses_intensity": True,
        "intensity_rates": {"intensive": 400, "moyenne": 180, "faible": 70},
        "builtin": True,
    },
    "ulm": {
        "label": "ULM / avion ultra-léger",
        "alpha": 1.0,
        "uses_intensity": True,
        "intensity_rates": {"intensive": 150, "moyenne": 60, "faible": 20},
        "builtin": True,
    },
    "planeur": {
        "label": "Planeur (vol à voile)",
        "alpha": 0.6,
        "uses_intensity": True,
        "intensity_rates": {"intensive": 250, "moyenne": 100, "faible": 30},
        "builtin": True,
    },
    "voltige": {
        "label": "Avion de voltige / acrobatie",
        "alpha": 1.7,
        "uses_intensity": True,
        "intensity_rates": {"intensive": 200, "moyenne": 90, "faible": 30},
        "builtin": True,
    },
    "warbird": {
        "label": "Avion ancien / warbird / collection",
        "alpha": 1.1,
        "uses_intensity": True,
        "intensity_rates": {"intensive": 60, "moyenne": 25, "faible": 8},
        "builtin": True,
    },
    "hydravion": {
        "label": "Hydravion / amphibie",
        "alpha": 1.3,
        "uses_intensity": True,
        "intensity_rates": {"intensive": 220, "moyenne": 100, "faible": 35},
        "builtin": True,
    },
    "helicopter": {
        "label": "Hélicoptère",
        "alpha": 2.2,
        "uses_intensity": False,
        "intensity_rates": None,
        "builtin": True,
    },
    "business_jet": {
        "label": "Jet d'affaires (Citation, Learjet, Falcon, Gulfstream...)",
        "alpha": 1.5,
        "uses_intensity": False,
        "intensity_rates": None,
        "builtin": True,
    },
    "regional_turboprop": {
        "label": "Turbopropulseur régional (ATR, Dash 8, Saab 340...)",
        "alpha": 1.9,
        "uses_intensity": False,
        "intensity_rates": None,
        "builtin": True,
    },
    "regional_jet": {
        "label": "Jet régional (CRJ, E-Jet...)",
        "alpha": 2.0,
        "uses_intensity": False,
        "intensity_rates": None,
        "builtin": True,
    },
    "narrow": {
        "label": "Monocouloir (A320/737 et familles similaires)",
        "alpha": 2.0,
        "uses_intensity": False,
        "intensity_rates": None,
        "builtin": True,
    },
    "wide": {
        "label": "Long-courrier gros porteur (A330/777/787...)",
        "alpha": 1.7,
        "uses_intensity": False,
        "intensity_rates": None,
        "builtin": True,
    },
    "super": {
        "label": "Très gros porteur (A380, 747...)",
        "alpha": 1.6,
        "uses_intensity": False,
        "intensity_rates": None,
        "builtin": True,
    },
    "cargo_lourd": {
        "label": "Gros cargo dédié (An-124, IL-76, C-5...)",
        "alpha": 1.4,
        "uses_intensity": False,
        "intensity_rates": None,
        "builtin": True,
    },
    "militaire": {
        "label": "Avion militaire (chasse / transport)",
        "alpha": 1.8,
        "uses_intensity": False,
        "intensity_rates": None,
        "builtin": True,
    },
}

INTENSITY_OPTIONS = [
    ("Intensive (usage très fréquent)", "intensive"),
    ("Moyenne (usage régulier)", "moyenne"),
    ("Faible (usage occasionnel)", "faible"),
]

# code ICAO d'avion -> code de catégorie (voir CATEGORY_DEFINITIONS)
AIRCRAFT_CATEGORIES_RAW = {
    "ga": [
        "C172", "C152", "C150", "C182", "C206", "C210",
        "P28A", "P28R", "P32R", "PA28", "PA34", "PA44",
        "DA40", "DA42", "SR20", "SR22", "SR2T",
        "BE33", "BE35", "BE36", "BE58", "M20P", "M20T",
        "AA5", "DR40", "DR22", "TB10", "TB20", "TB21",
    ],
    "ga_turbo": ["TBM7", "TBM8", "TBM9", "PC12", "BE20", "BE9L", "PAY2"],
    "ulm": ["ULAC", "SAVA", "PIPQ"],
    "planeur": ["GLID", "ASK21", "ASW27", "DG80", "LS8", "PIK20"],
    "voltige": ["EXTR", "SU29", "SU31", "PITS", "CAP1", "YAK5"],
    "warbird": ["SPIT", "P51", "T6", "YK11", "DC3"],
    "hydravion": ["DHC2", "DHC3", "PBY", "CL15"],
    "helicopter": ["R44", "R66", "EC20", "EC35", "EC45", "AS50", "B06", "B407", "H125", "H145"],
    "business_jet": ["C25A", "C25B", "C56X", "C680", "LJ45", "LJ60", "F2TH", "F900", "GLF4", "GLF5", "GL5T", "G650"],
    "regional_turboprop": ["AT43", "AT45", "AT72", "AT76", "DH8D", "DH8C", "SF34", "B190"],
    "regional_jet": ["CRJ2", "CRJ7", "CRJ9", "CRJX", "E170", "E175", "E190", "E195", "E290", "E295"],
    "narrow": [
        "A319", "A320", "A321", "A20N", "A21N",
        "B737", "B738", "B739", "B37M", "B38M", "B39M", "B3XM",
        "MD82", "MD83", "MD88", "MD90",
    ],
    "wide": [
        "A332", "A333", "A338", "A339", "A342", "A343", "A345", "A346",
        "A359", "A35K", "B762", "B763", "B764", "B772", "B773", "B77L",
        "B77W", "B788", "B789", "B78X", "MD11",
    ],
    "super": ["A388", "B742", "B743", "B744", "B748"],
    "cargo_lourd": ["A124", "IL76", "C5M", "C17"],
    "militaire": ["F16", "F15", "F18", "RFAL", "C130", "A400"],
}

AIRCRAFT_CODE_TO_CATEGORY = {}
for _cat, _codes in AIRCRAFT_CATEGORIES_RAW.items():
    for _code in _codes:
        AIRCRAFT_CODE_TO_CATEGORY[_code.upper()] = _cat


def append_category_to_csv(code, label, alpha, uses_intensity, rates):
    path = os.path.join(_script_dir(), "categories_extra.csv")
    is_new = not os.path.isfile(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["code", "label", "alpha", "uses_intensity",
                              "rate_intensive", "rate_moyenne", "rate_faible"])
        if uses_intensity:
            writer.writerow([code, label, alpha, 1, rates["intensive"], rates["moyenne"], rates["faible"]])
        else:
            writer.writerow([code, label, alpha, 0, "", "", ""])


# =====================================================================
#  3. CHARGEMENT DES FICHIERS CSV D'EXTENSION (facultatifs)
# =====================================================================

def load_extra_categories():
    path = os.path.join(_script_dir(), "categories_extra.csv")
    if not os.path.isfile(path):
        return 0
    count = 0
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.reader(f):
                if not row or row[0].strip().lower() in ("code", "#"):
                    continue
                row = row + [""] * (7 - len(row))
                code, label, alpha, uses_i, r_int, r_moy, r_faib = [c.strip() for c in row[:7]]
                if not code:
                    continue
                try:
                    alpha_val = float(alpha)
                except ValueError:
                    alpha_val = 1.5
                uses_intensity = uses_i in ("1", "true", "True", "vrai", "oui")
                rates = None
                if uses_intensity:
                    def _num(v, default):
                        try:
                            return int(float(v))
                        except ValueError:
                            return default
                    rates = {"intensive": _num(r_int, 200), "moyenne": _num(r_moy, 90), "faible": _num(r_faib, 30)}
                CATEGORY_DEFINITIONS[code.lower()] = {
                    "label": label or code, "alpha": alpha_val,
                    "uses_intensity": uses_intensity, "intensity_rates": rates, "builtin": False,
                }
                count += 1
    except Exception as exc:  # pragma: no cover
        print(f"[avertissement] categories_extra.csv ignoré : {exc}")
    return count


def load_extra_airlines():
    path = os.path.join(_script_dir(), "airlines_extra.csv")
    if not os.path.isfile(path):
        return 0
    count = 0
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.reader(f):
                if not row or row[0].strip().lower() in ("iata", "#"):
                    continue
                row = row + [""] * (4 - len(row))
                iata, icao, name, cat = [c.strip() for c in row[:4]]
                if not (iata or icao):
                    continue
                _register_airline(iata, icao, name or (iata or icao), cat.lower())
                count += 1
    except Exception as exc:  # pragma: no cover
        print(f"[avertissement] airlines_extra.csv ignoré : {exc}")
    return count


def load_extra_aircraft():
    path = os.path.join(_script_dir(), "aircraft_extra.csv")
    if not os.path.isfile(path):
        return 0
    count = 0
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.reader(f):
                if not row or row[0].strip().lower() in ("code_icao", "#"):
                    continue
                row = row + [""] * (2 - len(row))
                code, cat = [c.strip() for c in row[:2]]
                cat = cat.lower()
                if not code or cat not in CATEGORY_DEFINITIONS:
                    continue
                AIRCRAFT_CODE_TO_CATEGORY[code.upper()] = cat
                AIRCRAFT_CATEGORIES_RAW.setdefault(cat, []).append(code.upper())
                count += 1
    except Exception as exc:  # pragma: no cover
        print(f"[avertissement] aircraft_extra.csv ignoré : {exc}")
    return count


# ordre important : les catégories doivent être connues avant de
# valider les codes avions personnalisés
_nb_extra_categories = load_extra_categories()
_nb_extra_airlines = load_extra_airlines()
_nb_extra_aircraft = load_extra_aircraft()
for _n, _label in ((_nb_extra_categories, "categories_extra.csv"),
                    (_nb_extra_airlines, "airlines_extra.csv"),
                    (_nb_extra_aircraft, "aircraft_extra.csv")):
    if _n:
        print(f"[info] {_n} entrée(s) supplémentaire(s) chargée(s) depuis {_label}")


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

MAINTENANCE_DEFAULT_BY_ACTIVITY = {
    "lowcost": "bonne",
    "legacy": "excellente",
    "cargo": "normale",
    "regional": "normale",
    "charter": "normale",
    "other": "normale",
}

MAINTENANCE_MULTIPLIER = {"excellente": 0.7, "bonne": 0.85, "normale": 1.0, "mauvaise": 1.3}


def find_airline(code):
    code = (code or "").strip().upper()
    if not code:
        return None
    return AIRLINE_BY_ICAO.get(code) or AIRLINE_BY_IATA.get(code)


def detect_aircraft_category(type_code):
    return AIRCRAFT_CODE_TO_CATEGORY.get((type_code or "").strip().upper())


def estimate_cycle_rate(category_code, activity_code, intensity_code):
    cat = CATEGORY_DEFINITIONS.get(category_code)
    if cat and cat["uses_intensity"]:
        rates = cat["intensity_rates"] or {}
        return rates.get(intensity_code, next(iter(rates.values()), 100))
    return CYCLE_RATE_BY_ACTIVITY.get(activity_code, CYCLE_RATE_BY_ACTIVITY["other"])


def compute_human_age(age_years, cycles, category_code, maintenance_code):
    alpha = CATEGORY_DEFINITIONS.get(category_code, {}).get("alpha", 1.5)
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
    ("Autre / inconnu", "other"),
]

MAINTENANCE_OPTIONS = [
    ("Excellente", "excellente"),
    ("Bonne", "bonne"),
    ("Normale", "normale"),
    ("Mauvaise", "mauvaise"),
]


def _build_maps(options):
    return {label: code for label, code in options}, {code: label for label, code in options}


ACT_LABEL2CODE, ACT_CODE2LABEL = _build_maps(ACTIVITY_OPTIONS)
MAINT_LABEL2CODE, MAINT_CODE2LABEL = _build_maps(MAINTENANCE_OPTIONS)
INT_LABEL2CODE, INT_CODE2LABEL = _build_maps(INTENSITY_OPTIONS)

BG = "#f4f6fa"
CARD_BG = "#ffffff"
ACCENT = "#1f6feb"
TEXT_MUTED = "#5b6472"


class ScrollableFrame(ttk.Frame):
    """Cadre défilant verticalement : contient toute l'interface pour que
    rien ne soit coupé même avec beaucoup de sections."""

    def __init__(self, parent):
        super().__init__(parent, style="TFrame")
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = ttk.Frame(canvas, style="TFrame")

        def _sync_scrollregion(_evt=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        window_id = canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", _sync_scrollregion)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)


class App:
    def __init__(self, root):
        self.root = root
        root.title("✈️ Age Avion → Age Humain")
        root.configure(bg=BG)
        root.geometry("780x920")
        root.minsize(700, 600)

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
        style.configure("Header.TLabel", background=BG, foreground="#111827", font=("Segoe UI", 18, "bold"))
        style.configure("SubHeader.TLabel", background=BG, foreground=TEXT_MUTED, font=("Segoe UI", 10))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TCheckbutton", background=CARD_BG)

        # ---- variables ----------------------------------------------
        self.registration_var = tk.StringVar()
        self.airline_code_var = tk.StringVar()
        self.airline_status_var = tk.StringVar(value="Aucune compagnie recherchée pour l'instant.")

        self.new_air_iata_var = tk.StringVar()
        self.new_air_icao_var = tk.StringVar()
        self.new_air_name_var = tk.StringVar()
        self.new_air_activity_var = tk.StringVar(value=ACT_CODE2LABEL["other"])
        self.new_airline_status_var = tk.StringVar(value="")

        self.aircraft_code_var = tk.StringVar()
        self.is_glider_var = tk.BooleanVar(value=False)
        self.category_label_var = tk.StringVar()

        self.new_cat_name_var = tk.StringVar()
        self.new_cat_alpha_var = tk.StringVar(value="1.5")
        self.new_cat_is_club_var = tk.BooleanVar(value=False)
        self.new_cat_rate_intensive_var = tk.StringVar(value="200")
        self.new_cat_rate_moyenne_var = tk.StringVar(value="90")
        self.new_cat_rate_faible_var = tk.StringVar(value="30")
        self.new_category_status_var = tk.StringVar(value="")

        self.activity_label_var = tk.StringVar(value=ACT_CODE2LABEL["other"])
        self.maintenance_label_var = tk.StringVar(value=MAINT_CODE2LABEL["normale"])
        self.intensity_label_var = tk.StringVar(value=INT_CODE2LABEL["moyenne"])
        self.age_var = tk.StringVar()
        self.custom_cycles_enabled = tk.BooleanVar(value=False)
        self.custom_cycles_var = tk.StringVar()

        self.error_var = tk.StringVar(value="")
        self.result_title_var = tk.StringVar(value="—")
        self.result_details_var = tk.StringVar(value="Renseignez les champs ci-dessus puis cliquez sur Calculer.")
        self.export_status_var = tk.StringVar(value="")

        self._refresh_category_maps()
        self.category_label_var.set(self.cat_code2label["narrow"])

        self._build_layout()
        self._on_category_change()

    # ------------------------------------------------------------------
    #  Categories dynamiques (car on peut en créer de nouvelles)
    # ------------------------------------------------------------------
    def _refresh_category_maps(self):
        self.cat_label2code = {d["label"]: code for code, d in CATEGORY_DEFINITIONS.items()}
        self.cat_code2label = {code: d["label"] for code, d in CATEGORY_DEFINITIONS.items()}

    def _category_labels_sorted(self):
        return sorted(self.cat_label2code.keys())

    # ------------------------------------------------------------------
    #  Construction de l'interface
    # ------------------------------------------------------------------
    def _build_layout(self):
        header = ttk.Frame(self.root, style="TFrame")
        header.pack(fill="x", padx=20, pady=(14, 6))
        ttk.Label(header, text="✈️ Age Avion → Age Humain", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="Estimez l'âge « humain » d'un avion à partir de son type et de son exploitant.",
                  style="SubHeader.TLabel").pack(anchor="w")

        scroll = ScrollableFrame(self.root)
        scroll.pack(fill="both", expand=True, padx=(20, 4), pady=6)
        container = scroll.inner

        self._build_airline_section(container)
        self._build_new_airline_section(container)
        self._build_aircraft_section(container)
        self._build_new_category_section(container)
        self._build_operation_section(container)
        self._build_age_section(container)
        self._build_actions(container)
        self._build_result_section(container)
        self._build_history_section(container)

    def _card(self, parent, title):
        frame = ttk.LabelFrame(parent, text=title, style="Card.TLabelframe", padding=12)
        frame.pack(fill="x", pady=6, padx=2)
        return frame

    # ---- 1. Compagnie -------------------------------------------------
    def _build_airline_section(self, parent):
        card = self._card(parent, "1. Compagnie aérienne (optionnel)")
        card.grid_columnconfigure(1, weight=1)

        ttk.Label(card, text="Code IATA ou ICAO :", background=CARD_BG).grid(row=0, column=0, sticky="w", pady=3)
        entry = ttk.Entry(card, textvariable=self.airline_code_var, width=10)
        entry.grid(row=0, column=1, sticky="w", pady=3)
        entry.bind("<Return>", lambda e: self.on_airline_lookup())
        ttk.Button(card, text="Rechercher", command=self.on_airline_lookup).grid(row=0, column=2, sticky="w", padx=(8, 0))

        ttk.Label(card, textvariable=self.airline_status_var, style="Muted.TLabel", wraplength=640,
                  justify="left").grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))

        ttk.Label(card, text="Immatriculation (facultatif, pour vos notes) :", background=CARD_BG).grid(
            row=2, column=0, sticky="w", pady=(10, 3))
        ttk.Entry(card, textvariable=self.registration_var, width=12).grid(row=2, column=1, sticky="w", pady=(10, 3))

    # ---- 1b. Créer une compagnie ---------------------------------------
    def _build_new_airline_section(self, parent):
        card = self._card(parent, "1b. Créer une compagnie personnalisée (si elle n'est pas dans la liste)")
        card.grid_columnconfigure(5, weight=1)

        ttk.Label(card, text="IATA :", background=CARD_BG).grid(row=0, column=0, sticky="w")
        ttk.Entry(card, textvariable=self.new_air_iata_var, width=6).grid(row=0, column=1, sticky="w", padx=(2, 10))
        ttk.Label(card, text="ICAO :", background=CARD_BG).grid(row=0, column=2, sticky="w")
        ttk.Entry(card, textvariable=self.new_air_icao_var, width=6).grid(row=0, column=3, sticky="w", padx=(2, 10))
        ttk.Label(card, text="Nom :", background=CARD_BG).grid(row=0, column=4, sticky="w")
        ttk.Entry(card, textvariable=self.new_air_name_var, width=26).grid(row=0, column=5, sticky="we", padx=(2, 0))

        ttk.Label(card, text="Type d'activité :", background=CARD_BG).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Combobox(card, textvariable=self.new_air_activity_var, values=[l for l, _ in ACTIVITY_OPTIONS],
                     state="readonly", width=26).grid(row=1, column=2, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Button(card, text="Enregistrer la compagnie", command=self.on_create_airline).grid(
            row=1, column=5, sticky="e", pady=(8, 0))

        ttk.Label(card, textvariable=self.new_airline_status_var, style="Muted.TLabel", wraplength=640,
                  justify="left").grid(row=2, column=0, columnspan=6, sticky="w", pady=(6, 0))

    # ---- 2. Avion -------------------------------------------------------
    def _build_aircraft_section(self, parent):
        card = self._card(parent, "2. Avion")
        card.grid_columnconfigure(1, weight=1)

        ttk.Label(card, text="Code type ICAO :", background=CARD_BG).grid(row=0, column=0, sticky="w", pady=3)
        codes = sorted(AIRCRAFT_CODE_TO_CATEGORY.keys())
        self.aircraft_combo = ttk.Combobox(card, textvariable=self.aircraft_code_var, values=codes, width=12)
        self.aircraft_combo.grid(row=0, column=1, sticky="w", pady=3)
        self.aircraft_combo.bind("<<ComboboxSelected>>", lambda e: self.on_aircraft_type_change())
        self.aircraft_combo.bind("<FocusOut>", lambda e: self.on_aircraft_type_change())
        self.aircraft_combo.bind("<Return>", lambda e: self.on_aircraft_type_change())

        ttk.Checkbutton(card, text="C'est un planeur (pas de code ICAO à saisir)",
                         variable=self.is_glider_var, command=self.on_glider_toggle).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(2, 6))

        ttk.Label(card, text="Catégorie :", background=CARD_BG).grid(row=2, column=0, sticky="w", pady=3)
        self.category_combo = ttk.Combobox(card, textvariable=self.category_label_var,
                                            values=self._category_labels_sorted(), state="readonly", width=48)
        self.category_combo.grid(row=2, column=1, columnspan=2, sticky="we", pady=3)
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self._on_category_change())

        ttk.Label(card, text="(la catégorie est proposée automatiquement à partir du code ICAO,\n"
                              "mais vous pouvez toujours la changer vous-même)",
                  style="Muted.TLabel", justify="left").grid(row=3, column=0, columnspan=3, sticky="w")

    # ---- 2b. Créer une catégorie ---------------------------------------
    def _build_new_category_section(self, parent):
        card = self._card(parent, "2b. Créer une catégorie d'avion personnalisée")
        card.grid_columnconfigure(1, weight=1)

        ttk.Label(card, text="Nom de la catégorie :", background=CARD_BG).grid(row=0, column=0, sticky="w")
        ttk.Entry(card, textvariable=self.new_cat_name_var, width=36).grid(row=0, column=1, sticky="w", padx=(4, 0))

        ttk.Label(card, text="Coefficient de vieillissement (alpha) :", background=CARD_BG).grid(
            row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(card, textvariable=self.new_cat_alpha_var, width=8).grid(row=1, column=1, sticky="w", padx=(4, 0), pady=(4, 0))
        ttk.Label(card, text="(indicatif : ~0.6 pour un planeur, ~1.2 pour un avion léger,\n"
                              "~2.0 pour un avion de ligne — plus haut = vieillit plus vite)",
                  style="Muted.TLabel", justify="left").grid(row=2, column=0, columnspan=2, sticky="w")

        ttk.Checkbutton(card, text="Catégorie de type club/privé (utilise une intensité plutôt qu'une compagnie)",
                         variable=self.new_cat_is_club_var, command=self._on_new_cat_club_toggle).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(8, 2))

        self.new_cat_rates_frame = ttk.Frame(card, style="TFrame")
        self.new_cat_rates_frame.configure(style="TFrame")
        self.new_cat_rates_frame.grid(row=4, column=0, columnspan=2, sticky="w")
        for i, (lbl, var) in enumerate([
            ("Cycles/an intensive :", self.new_cat_rate_intensive_var),
            ("Cycles/an moyenne :", self.new_cat_rate_moyenne_var),
            ("Cycles/an faible :", self.new_cat_rate_faible_var),
        ]):
            ttk.Label(self.new_cat_rates_frame, text=lbl, background=CARD_BG).grid(row=0, column=2 * i, sticky="w", padx=(0 if i == 0 else 10, 2))
            ttk.Entry(self.new_cat_rates_frame, textvariable=var, width=6).grid(row=0, column=2 * i + 1, sticky="w")
        self.new_cat_rates_frame.grid_remove()

        ttk.Button(card, text="Créer la catégorie", command=self.on_create_category).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(10, 2))
        ttk.Label(card, textvariable=self.new_category_status_var, style="Muted.TLabel", wraplength=640,
                  justify="left").grid(row=6, column=0, columnspan=2, sticky="w")

    # ---- 3. Activité / maintenance -------------------------------------
    def _build_operation_section(self, parent):
        card = self._card(parent, "3. Exploitation et maintenance")
        card.grid_columnconfigure(1, weight=1)

        self.activity_frame = ttk.Frame(card, style="TFrame")
        self.activity_frame.configure(style="TFrame")
        self.activity_frame.grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(self.activity_frame, text="Type d'activité :", background=CARD_BG).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Combobox(self.activity_frame, textvariable=self.activity_label_var,
                     values=[l for l, _ in ACTIVITY_OPTIONS], state="readonly", width=32).grid(
            row=0, column=1, sticky="w", pady=3, padx=(8, 0))

        self.intensity_frame = ttk.Frame(card, style="TFrame")
        self.intensity_frame.configure(style="TFrame")
        self.intensity_frame.grid(row=1, column=0, columnspan=3, sticky="w")
        self.intensity_caption_var = tk.StringVar(value="Intensité d'utilisation :")
        ttk.Label(self.intensity_frame, textvariable=self.intensity_caption_var, background=CARD_BG).grid(
            row=0, column=0, sticky="w", pady=3)
        ttk.Combobox(self.intensity_frame, textvariable=self.intensity_label_var,
                     values=[l for l, _ in INTENSITY_OPTIONS], state="readonly", width=32).grid(
            row=0, column=1, sticky="w", pady=3, padx=(8, 0))

        ttk.Label(card, text="Qualité de maintenance :", background=CARD_BG).grid(row=2, column=0, sticky="w", pady=3)
        ttk.Combobox(card, textvariable=self.maintenance_label_var, values=[l for l, _ in MAINTENANCE_OPTIONS],
                     state="readonly", width=20).grid(row=2, column=1, sticky="w", pady=3)

        ttk.Checkbutton(card, text="Utiliser un nombre de cycles personnalisé",
                         variable=self.custom_cycles_enabled, command=self._on_custom_cycles_toggle).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(8, 2))
        self.cycles_entry = ttk.Entry(card, textvariable=self.custom_cycles_var, width=12, state="disabled")
        self.cycles_entry.grid(row=4, column=0, sticky="w")
        ttk.Label(card, text="(nombre total de cycles décollage/atterrissage connu de l'avion)",
                  style="Muted.TLabel").grid(row=4, column=1, sticky="w")

    # ---- 4. Âge ----------------------------------------------------------
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
        headers = {"heure": "Heure", "immat": "Immat.", "compagnie": "Compagnie",
                   "avion": "Type avion", "age": "Âge (ans)", "age_humain": "Âge humain"}
        widths = {"heure": 70, "immat": 70, "compagnie": 150, "avion": 90, "age": 70, "age_humain": 90}
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
                f"Compagnie « {code.strip().upper()} » non trouvée. Continuez en mode manuel ci-dessous, "
                f"ou créez-la vous-même dans la section 1b."
            )
            return
        self.airline_status_var.set(
            f"Trouvé : {airline['name']}  (IATA {airline['iata'] or '—'} / ICAO {airline['icao'] or '—'}) "
            f"— activité : {ACT_CODE2LABEL.get(airline['category'], airline['category'])}."
        )
        self.activity_label_var.set(ACT_CODE2LABEL.get(airline["category"], ACT_CODE2LABEL["other"]))
        default_maint = MAINTENANCE_DEFAULT_BY_ACTIVITY.get(airline["category"], "normale")
        self.maintenance_label_var.set(MAINT_CODE2LABEL[default_maint])

    def on_create_airline(self):
        iata = self.new_air_iata_var.get().strip().upper()
        icao = self.new_air_icao_var.get().strip().upper()
        name = self.new_air_name_var.get().strip()
        activity_code = ACT_LABEL2CODE.get(self.new_air_activity_var.get(), "other")
        if not (iata or icao):
            self.new_airline_status_var.set("Indiquez au moins un code IATA ou ICAO pour créer la compagnie.")
            return
        if not name:
            self.new_airline_status_var.set("Indiquez un nom pour la compagnie.")
            return
        _register_airline(iata, icao, name, activity_code)
        try:
            append_airline_to_csv(iata, icao, name, activity_code)
            saved_msg = "sauvegardée dans airlines_extra.csv"
        except OSError as exc:
            saved_msg = f"non sauvegardée sur disque ({exc})"
        self.new_airline_status_var.set(
            f"Compagnie « {name} » ({iata or '—'}/{icao or '—'}) ajoutée et {saved_msg}. "
            f"Vous pouvez déjà la rechercher dans la section 1."
        )
        self.new_air_iata_var.set("")
        self.new_air_icao_var.set("")
        self.new_air_name_var.set("")

    def on_glider_toggle(self):
        if self.is_glider_var.get():
            self.aircraft_code_var.set("")
            self.aircraft_combo.configure(state="disabled")
            self.category_label_var.set(self.cat_code2label["planeur"])
            self.category_combo.configure(state="disabled")
        else:
            self.aircraft_combo.configure(state="normal")
            self.category_combo.configure(state="readonly")
        self._on_category_change()

    def on_aircraft_type_change(self):
        if self.is_glider_var.get():
            return
        code = self.aircraft_code_var.get()
        category = detect_aircraft_category(code)
        if category:
            self.category_label_var.set(self.cat_code2label[category])
            self._on_category_change()
        elif code.strip():
            self.error_var.set(
                f"Type d'avion « {code.strip().upper()} » non reconnu : choisissez la catégorie "
                f"manuellement ci-dessus (ou créez-la / ajoutez le code via un CSV)."
            )

    def _on_category_change(self):
        code = self.cat_label2code.get(self.category_label_var.get())
        cat = CATEGORY_DEFINITIONS.get(code, {})
        if cat.get("uses_intensity"):
            self.intensity_frame.grid()
            self.activity_frame.grid_remove()
            self.intensity_caption_var.set(f"Intensité d'utilisation ({cat['label'].split('(')[0].strip()}) :")
        else:
            self.intensity_frame.grid_remove()
            self.activity_frame.grid()

    def _on_new_cat_club_toggle(self):
        if self.new_cat_is_club_var.get():
            self.new_cat_rates_frame.grid()
        else:
            self.new_cat_rates_frame.grid_remove()

    def on_create_category(self):
        name = self.new_cat_name_var.get().strip()
        if not name:
            self.new_category_status_var.set("Donnez un nom à la nouvelle catégorie.")
            return
        try:
            alpha = float(self.new_cat_alpha_var.get().strip().replace(",", "."))
        except ValueError:
            self.new_category_status_var.set("Le coefficient de vieillissement doit être un nombre (ex : 1.5).")
            return

        is_club = self.new_cat_is_club_var.get()
        rates = None
        if is_club:
            try:
                rates = {
                    "intensive": int(float(self.new_cat_rate_intensive_var.get())),
                    "moyenne": int(float(self.new_cat_rate_moyenne_var.get())),
                    "faible": int(float(self.new_cat_rate_faible_var.get())),
                }
            except ValueError:
                self.new_category_status_var.set("Les taux d'intensité doivent être des nombres entiers.")
                return

        code = slugify(name, existing_keys=CATEGORY_DEFINITIONS.keys())
        CATEGORY_DEFINITIONS[code] = {
            "label": name, "alpha": alpha, "uses_intensity": is_club,
            "intensity_rates": rates, "builtin": False,
        }
        self._refresh_category_maps()
        self.category_combo.configure(values=self._category_labels_sorted())
        self.category_label_var.set(name)
        if not self.is_glider_var.get():
            self.category_combo.configure(state="readonly")
        self._on_category_change()

        try:
            append_category_to_csv(code, name, alpha, is_club, rates)
            saved_msg = "sauvegardée dans categories_extra.csv"
        except OSError as exc:
            saved_msg = f"non sauvegardée sur disque ({exc})"
        self.new_category_status_var.set(f"Catégorie « {name} » créée, sélectionnée ci-dessus, et {saved_msg}.")
        self.new_cat_name_var.set("")
        self.new_cat_alpha_var.set("1.5")

    def _on_custom_cycles_toggle(self):
        self.cycles_entry.configure(state="normal" if self.custom_cycles_enabled.get() else "disabled")

    def on_reset(self):
        self.registration_var.set("")
        self.airline_code_var.set("")
        self.airline_status_var.set("Aucune compagnie recherchée pour l'instant.")
        self.is_glider_var.set(False)
        self.aircraft_combo.configure(state="normal")
        self.category_combo.configure(state="readonly")
        self.aircraft_code_var.set("")
        self.category_label_var.set(self.cat_code2label["narrow"])
        self.activity_label_var.set(ACT_CODE2LABEL["other"])
        self.maintenance_label_var.set(MAINT_CODE2LABEL["normale"])
        self.intensity_label_var.set(INT_CODE2LABEL["moyenne"])
        self.age_var.set("")
        self.custom_cycles_enabled.set(False)
        self.custom_cycles_var.set("")
        self._on_custom_cycles_toggle()
        self._on_category_change()
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

        category_code = self.cat_label2code.get(self.category_label_var.get(), "narrow")
        activity_code = ACT_LABEL2CODE.get(self.activity_label_var.get(), "other")
        maintenance_code = MAINT_LABEL2CODE.get(self.maintenance_label_var.get(), "normale")
        intensity_code = INT_LABEL2CODE.get(self.intensity_label_var.get(), "moyenne")

        if self.custom_cycles_enabled.get():
            try:
                cycles = int(float(self.custom_cycles_var.get().strip()))
                if cycles < 0:
                    raise ValueError
            except ValueError:
                self.error_var.set("Le nombre de cycles personnalisé doit être un entier positif.")
                return
        else:
            rate = estimate_cycle_rate(category_code, activity_code, intensity_code)
            cycles = int(age * rate)

        human_age = compute_human_age(age, cycles, category_code, maintenance_code)
        verdict_text, verdict_color = verdict_for_human_age(human_age)

        self.result_title_var.set(f"{human_age} ans (âge humain)")
        self.result_title_label.configure(fg=verdict_color)

        airline = find_airline(self.airline_code_var.get())
        cat_def = CATEGORY_DEFINITIONS.get(category_code, {})
        exploitant = airline["name"] if airline else (
            "— (mode manuel)" if not cat_def.get("uses_intensity") else "— (usage privé/club)"
        )

        details = (
            f"{verdict_text}\n"
            f"Compagnie/exploitant : {exploitant}   |   Catégorie : {self.category_label_var.get()}\n"
        )
        if cat_def.get("uses_intensity"):
            details += f"Intensité : {self.intensity_label_var.get()}"
        else:
            details += f"Type d'activité : {self.activity_label_var.get()}"
        details += (
            f"\nMaintenance : {self.maintenance_label_var.get()}   |   "
            f"Cycles estimés : {cycles}   |   Âge réel : {age} ans"
        )
        self.result_details_var.set(details)

        self._last_result = {
            "heure": time.strftime("%H:%M:%S"),
            "immat": self.registration_var.get().strip().upper() or "—",
            "compagnie": exploitant,
            "avion": ("PLANEUR" if self.is_glider_var.get() else self.aircraft_code_var.get().strip().upper()) or "—",
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
                        f"Exploitant={r['compagnie']} Age={r['age']} -> AgeHumain={r['age_humain']}\n")
                f.write(f"    {r['details'].replace(chr(10), ' | ')}\n\n")
            self.export_status_var.set(f"Résultat ajouté à : {path}")
        except OSError as exc:
            self.error_var.set(f"Impossible d'écrire le fichier d'export : {exc}")


# =====================================================================
#  6. NOTE SUR LA BASE OFFICIELLE ICAO DOC 8643
# =====================================================================
# La base complète et officielle des désignateurs de type d'aéronef
# (ICAO Doc 8643) n'est pas librement téléchargeable (moteur de
# recherche en ligne restreint, ou PDF payant, sans export CSV
# public). La liste embarquée ci-dessus couvre les catégories les
# plus courantes et peut être complétée à tout moment via
# "aircraft_extra.csv" (voir en tête de fichier), par exemple en
# copiant les codes trouvés un par un sur le site de recherche ICAO.


# =====================================================================
#  MAIN
# =====================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
