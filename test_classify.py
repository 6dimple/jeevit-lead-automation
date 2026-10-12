import json
from pathlib import Path
from leads_clean import clean_lead
from dedupe import load_existing, check_duplicates
from classify import classify_lead

existing = load_existing(Path("data") / "existing_leads.csv")
with open(Path("data") / "incoming_leads.json", encoding="utf-8") as f:
    incoming = json.load(f)
leads = check_duplicates([clean_lead(r) for r in incoming], existing)

for l in leads:
    # Skip leads that cannot be processed anyway
    if l["dup_status"] == "unchecked" or "empty_message" in l["issues"] or l["dup_status"] == "duplicate_batch":
        print(f"{l['id']} | SKIPPED ({l['dup_status']}, {l['issues']})")
        continue
    r = classify_lead(l)
    print(f"{l['id']} | {l['dup_status']:<18} | {r['status']:<12} | {r['tag']:<5} | flags={r['flags']} | via {r['provider']}")
    if r["reply"]:
        print(f"       reply: {r['reply']}")