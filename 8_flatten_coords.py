# iterates over all .json files in folder, extracts surface data
# flattens 
#  writes to a single CSV (one row per building).

"""
Flatten coordinates: one CSV row == one *physical* surface.
Handles façade explosions (1 F object ⇒ several F faces).
"""
import os, json, csv, itertools
import pandas as pd

# ── CONFIG ───────────────────────────────────────────────────────────────────
INPUT_DIR      = "7A_enriched_perPand_21"       # folder with Pand JSON files
OUTPUT_CSV     = "8A_flattened_surfaces_21.csv"
OUTPUT_EXCEL   = "8B_flattened_surfaces_21.xlsx"
PAD_VALUE      = -1                             # value for missing items
# ─────────────────────────────────────────────────────────────────────────────

def explode_surfaces(s):
    """
    Yield one dict per *physical* surface.

    * Ground (G) and Roof (R) are returned as-is.
    * Façades (F) are split: every **two** consecutive distances / unit-pairs
      form one façade face (len(distances)//2 faces).
    """
    if s.get("Type") != "F":
        yield s
        return

    d  = s.get("Distances",   [])
    up = s.get("UnitPairs",   [])

    # number of façade faces = number of edges = len(distances)//2
    n_faces = max(1, len(d) // 2)
    for i in range(n_faces):
        face = {
            **s,  # copy centroid etc.
            "Distances" : d [2*i : 2*i + 2],
            "UnitPairs" : up[2*i : 2*i + 2],
        }
        yield face

def main():
    # 1) First scan – work out widest face AFTER exploding
    max_dists = max_units = 0
    for fn in os.listdir(INPUT_DIR):
        if not fn.lower().endswith(".json"):
            continue
        with open(os.path.join(INPUT_DIR, fn), encoding="utf-8") as f:
            b = json.load(f)
        for s in b.get("Surfaces", []):
            for face in explode_surfaces(s):
                max_dists = max(max_dists, len(face.get("Distances", [])))
                max_units = max(max_units, len(face.get("UnitPairs", [])))

    # 2) Build header
    base_cols = [
        "Pand ID","Archetype ID","Construction Year","Floor Area","Number of Floors",
        "Wall Area","Roof Area (Flat)","Roof Area (Sloped)","Shared Wall Area",
        "Absolute Height (70%)","Annual Heating [kWh/m2]","Annual Cooling [kWh/m2]",
        "Surface Index","Surface Type","Centroid X","Centroid Y"
    ]
    dist_cols = [f"d{i+1}"            for i in range(max_dists)]
    unit_cols = list(itertools.chain.from_iterable(
                    (f"ux{i+1}", f"uy{i+1}") for i in range(max_units)))
    header    = base_cols + dist_cols + unit_cols

    # 3) Collect rows
    rows = []
    for fn in os.listdir(INPUT_DIR):
        if not fn.lower().endswith(".json"):
            continue
        with open(os.path.join(INPUT_DIR, fn), encoding="utf-8") as f:
            b = json.load(f)

        heat = b.get("Annual Heating [kWh/m2]",
               b.get("simulation_results",{}).get("Annual Heating [kWh/m2]"))
        cool = b.get("Annual Cooling [kWh/m2]",
               b.get("simulation_results",{}).get("Annual Cooling [kWh/m2]"))

        meta = [
            b.get("Pand ID"), b.get("Archetype ID"), b.get("Construction Year"),
            b.get("Floor Area"), b.get("Number of Floors"), b.get("Wall Area"),
            b.get("Roof Area (Flat)"), b.get("Roof Area (Sloped)"), b.get("Shared Wall Area"),
            b.get("Absolute Height (70%)"), heat, cool
        ]

        surf_idx = 0
        for s in b.get("Surfaces", []):
            for face in explode_surfaces(s):
                centroid = face.get("Centroid", {})
                dists    = face.get("Distances", [])
                units2d  = list(itertools.chain.from_iterable(face.get("UnitPairs", [])))

                row = (
                    meta +
                    [surf_idx, face.get("Type"),
                     centroid.get("x", PAD_VALUE), centroid.get("y", PAD_VALUE)] +
                    dists  + [PAD_VALUE]*(max_dists - len(dists)) +
                    units2d + [PAD_VALUE]*(max_units*2 - len(units2d))
                )
                rows.append(row)
                surf_idx += 1

    # 4) Write outputs
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f_csv:
        csv.writer(f_csv).writerows([header, *rows])

    pd.DataFrame(rows, columns=header).to_excel(OUTPUT_EXCEL, index=False)
    print("Created:", OUTPUT_CSV, "and", OUTPUT_EXCEL)

if __name__ == "__main__":
    main()
    print(f"written {OUTPUT_CSV}")
    print(f"written {OUTPUT_EXCEL}")