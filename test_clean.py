import json
from pathlib import Path
from leads_clean import clean_lead

with open(Path("data") / "incoming_leads.json", encoding="utf-8") as f:
    incoming = json.load(f)

for raw in incoming:
    c = clean_lead(raw)
    print(f"{c['id']} | {c['name']:<16} | {c['email']:<32} | key={c['email_key']:<30} | issues={c['issues']}")