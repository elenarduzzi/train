# write a new json file with level 01 input features, vertex data
# reads .eso file, output heating and cooling demands per floor area. 

import os
import json

# files
input_folder = '2A_pand_surfaces_21_ML'
energy_json_path = '6A_energy_outputs_per_area_21.json'
output_folder = '7A_enriched_perPand_21'

os.makedirs(output_folder, exist_ok=True)

# === LOAD ENERGY DATA ===
with open(energy_json_path, "r") as f:
    energy_data = json.load(f)["buildings"]

energy_lookup = {
    b["Pand ID"]: {
        "Annual Heating [kWh/m2]": b["Annual Heating [kWh/m2]"],
        "Annual Cooling [kWh/m2]": b["Annual Cooling [kWh/m2]"]
    }
    for b in energy_data
}

# === PROCESS EACH FILE ===
for filename in os.listdir(input_folder):
    if not filename.endswith(".json"):
        continue

    path = os.path.join(input_folder, filename)
    with open(path, "r") as f:
        building_data = json.load(f)

    pand_id = building_data["Pand ID"]
    energy = energy_lookup.get(pand_id)

    if not energy:
        print(f"No energy data for {pand_id}, skipping.")
        continue

    enriched = building_data.copy()
    enriched.update(energy)

    # Write enriched file
    out_path = os.path.join(output_folder, f"{pand_id}.json")
    with open(out_path, "w") as f:
        json.dump(enriched, f, indent=4)

    print(f"Enriched JSON written for {pand_id}")

print("All done.")
