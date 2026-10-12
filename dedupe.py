import csv
from pathlib import Path

from leads_clean import clean_email, make_email_key


def load_existing(path):
    """Read existing_leads.csv and return the rows as a list of dictionaries."""
    with open(Path(path), "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def check_duplicates(leads, existing_rows):
    """
    Mark every cleaned lead as one of:
      new                 - not seen before, safe to add
      duplicate_existing  - already in the sheet (e.g. S-02 matches L-1001)
      duplicate_batch     - already appeared earlier in this same batch (e.g. S-14 matches S-12)
      unchecked           - no usable email, so we cannot compare
    """
    # key -> {"id": ..., "source": "existing" or "batch", "tag": ...}
    seen = {}
    for row in existing_rows:
        key = make_email_key(clean_email(row["email"]))
        seen[key] = {"id": row["lead_id"], "source": "existing", "tag": row["tag"]}

    by_id = {lead["id"]: lead for lead in leads}

    for lead in leads:
        lead["extra_messages"] = []      # extra info merged from later duplicates
        lead["duplicate_of"] = ""
        lead["existing_tag"] = ""

        key = lead["email_key"]

        if not key:
            lead["dup_status"] = "unchecked"
            continue

        if key not in seen:
            lead["dup_status"] = "new"
            seen[key] = {"id": lead["id"], "source": "batch", "tag": ""}
            continue

        match = seen[key]
        lead["duplicate_of"] = match["id"]

        if match["source"] == "existing":
            lead["dup_status"] = "duplicate_existing"
            lead["existing_tag"] = match["tag"]
        else:
            lead["dup_status"] = "duplicate_batch"
            # Keep the first lead, but don't lose what the second one said
            if lead["message"]:
                by_id[match["id"]]["extra_messages"].append(lead["message"])

    return leads