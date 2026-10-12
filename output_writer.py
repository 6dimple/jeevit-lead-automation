import csv
from pathlib import Path

OUT = Path("output")

SHEET_COLUMNS = ["lead_id", "name", "email", "company", "source", "tag",
                 "created_at", "draft_reply", "status", "notes"]
PROBLEM_COLUMNS = ["received_id", "name", "email", "company", "problem_type",
                   "reason", "action_needed", "original_submission"]


def write_csv(path, columns, rows):
    OUT.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_final_sheet(existing_rows, new_rows):
    rows = []
    for r in existing_rows:
        rows.append({**r, "draft_reply": "", "status": "existing", "notes": ""})
    rows.extend(new_rows)
    write_csv(OUT / "leads_final.csv", SHEET_COLUMNS, rows)


def write_problems(problem_rows):
    write_csv(OUT / "problems.csv", PROBLEM_COLUMNS, problem_rows)