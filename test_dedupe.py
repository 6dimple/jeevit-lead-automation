import json
from pathlib import Path
from leads_clean import clean_lead
from dedupe import load_existing, check_duplicates

existing = load_existing(Path("data") / "existing_leads.csv")
with open(Path("data") / "incoming_leads.json", encoding="utf-8") as f:
    incoming = json.load(f)

leads = check_duplicates([clean_lead(r) for r in incoming], existing)

for l in leads:
    print(f"{l['id']} | {l['name']:<16} | {l['dup_status']:<19} | matches={l['duplicate_of']:<7} | existing_tag={l['existing_tag']}")

print()
for l in leads:
    if l["extra_messages"]:
        print(f"{l['id']} merged extra messages: {l['extra_messages']}")