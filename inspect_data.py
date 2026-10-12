
import csv
import json
from pathlib import Path

# 1. Locate the data files
data_folder = Path("data")

existing_file = data_folder / "existing_leads.csv"
incoming_file = data_folder / "incoming_leads.json"

# 2. Load existing leads from the CSV file
with open(existing_file, "r", encoding="utf-8-sig", newline="") as file:
    existing_leads = list(csv.DictReader(file))

# 3. Load new leads from the JSON file
with open(incoming_file, "r", encoding="utf-8") as file:
    incoming_leads = json.load(file)

# 4. Display basic information
print("EXISTING LEADS")
print("Total records:", len(existing_leads))
print("Columns:", list(existing_leads[0].keys()) if existing_leads else [])

print("\nINCOMING LEADS")
print("Total records:", len(incoming_leads))

# 5. Display the first three incoming leads
print("\nFirst four incoming leads:")
for lead in incoming_leads[:4]:
    print(lead)
