# iterates over all .json files in folder, extracts surface data
# flattens 
#  writes to a single CSV (one row per building).
import os, json, csv, itertools
import pandas as pd

# ── CONFIG ──────────────────────────────────────────────────────────────────────
INPUT_DIR      = "7A_enriched_perPand_21"     # folder with Pand JSONs
OUTPUT_CSV     = "8A_flattened_surfaces_21.csv"
OUTPUT_EXCEL   = "8B_flattened_surfaces_21.xlsx"
PAD_VALUE      = -1                           # value to pad missing items
# ────────────────────────────────────────────────────────────────────────────────

# 1) Scan once to find the global maxima
max_dists = 0
max_units = 0           # number of (ux,uy) pairs
for fname in os.listdir(INPUT_DIR):
    if not fname.lower().endswith(".json"):
        continue
    with open(os.path.join(INPUT_DIR, fname), encoding="utf-8") as f:
        j = json.load(f)
    for s in j.get("Surfaces", []):
        max_dists = max(max_dists, len(s.get("Distances", [])))
        max_units = max(max_units, len(s.get("UnitPairs", [])))

# 2) Build header to match your example
base_cols = [
    "Pand ID","Archetype ID","Construction Year","Floor Area","Number of Floors",
    "Wall Area","Roof Area (Flat)","Roof Area (Sloped)","Shared Wall Area",
    "Absolute Height (70%)","Annual Heating [kWh/m2]","Annual Cooling [kWh/m2]",
    "Surface Index","Surface Type","Centroid X","Centroid Y"
]
dist_cols = [f"d{i+1}"  for i in range(max_dists)]
unit_cols = list(itertools.chain.from_iterable((f"ux{i+1}", f"uy{i+1}") for i in range(max_units)))
header    = base_cols + dist_cols + unit_cols

# 3) Collect rows
rows = []
for fname in os.listdir(INPUT_DIR):
    if not fname.lower().endswith(".json"):
        continue
    with open(os.path.join(INPUT_DIR, fname), encoding="utf-8") as f:
        b = json.load(f)

    # Heating/Cooling may be top-level OR inside "simulation_results"
    heat =  b.get("Annual Heating [kWh/m2]",
             b.get("simulation_results",{}).get("Annual Heating [kWh/m2]"))
    cool =  b.get("Annual Cooling [kWh/m2]",
             b.get("simulation_results",{}).get("Annual Cooling [kWh/m2]"))

    meta = [
        b.get("Pand ID"), b.get("Archetype ID"), b.get("Construction Year"),
        b.get("Floor Area"), b.get("Number of Floors"), b.get("Wall Area"),
        b.get("Roof Area (Flat)"), b.get("Roof Area (Sloped)"), b.get("Shared Wall Area"),
        b.get("Absolute Height (70%)"), heat, cool
    ]

    for idx, s in enumerate(b.get("Surfaces", [])):
        centroid = s.get("Centroid", {})
        dists    = s.get("Distances", [])
        units2d  = list(itertools.chain.from_iterable(s.get("UnitPairs", [])))

        row = (
            meta +
            [idx, s.get("Type"), centroid.get("x", PAD_VALUE), centroid.get("y", PAD_VALUE)] +
            dists  + [PAD_VALUE]*(max_dists - len(dists)) +
            units2d + [PAD_VALUE]*(max_units*2 - len(units2d))
        )
        rows.append(row)

# 4) Write CSV
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f_csv:
    writer = csv.writer(f_csv)
    writer.writerow(header)
    writer.writerows(rows)

# 5) Write Excel
pd.DataFrame(rows, columns=header).to_excel(OUTPUT_EXCEL, index=False)

print("Created:", OUTPUT_CSV, "and", OUTPUT_EXCEL)
