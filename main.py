import json
import logging
from collections import Counter
from pathlib import Path

from leads_clean import clean_lead
from dedupe import load_existing, check_duplicates
from classify import classify_lead
from notify import notify_hot
from output_writer import write_final_sheet, write_problems

DATA = Path("data")
Path("output").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[logging.FileHandler("output/run.log", mode="w", encoding="utf-8"),
              logging.StreamHandler()])
log = logging.getLogger("leads")

ACTIONS = {
    "missing_email": "Contact the lead another way (check phone/message) or ask them to resubmit with an email.",
    "invalid_email": "Fix the email address (do not guess), then resubmit.",
    "empty_message": "Lead sent no message. Reach out manually to ask what they need.",
    "duplicate_batch": "No action. Info was merged into the first submission.",
    "duplicate_existing": "No new row added. Check the existing lead.",
    "spam": "None. Rejected as spam.",
    "prompt_injection": "Human review. Message tried to instruct the AI. Do not send an automated reply.",
    "llm_failure": "Retry later or tag manually.",
    "unexpected_error": "Developer should check run.log.",
}



def process_lead(lead, raw, next_id, problems, new_rows):
    """Handle ONE lead. Returns True if a new row was added to the sheet."""
    lid = lead["id"]

    def problem(ptype, reason):
        problems.append({
            "received_id": lid, "name": lead["name"], "email": lead["email"],
            "company": lead["company"], "problem_type": ptype, "reason": reason,
            "action_needed": ACTIONS.get(ptype, ""),
            "original_submission": json.dumps(raw, ensure_ascii=False)})
        log.warning("%s | %s | %s", lid, ptype, reason)

    # 1. Cannot be identified: bad or missing email
    if "missing_email" in lead["issues"]:
        return problem("missing_email", "No email address provided.")
    if "invalid_email" in lead["issues"]:
        return problem("invalid_email", f"Email '{lead['email']}' is not a valid address.")

    # 2. Duplicate inside this batch
    if lead["dup_status"] == "duplicate_batch":
        return problem("duplicate_batch",
                       f"Same person as {lead['duplicate_of']} in this batch. Extra message merged into it.")

    # 3. Nothing to score
    if "empty_message" in lead["issues"] and lead["dup_status"] == "new":
        return problem("empty_message", "Message was empty, so it cannot be tagged.")

    # 4. LLM step (new leads and duplicates of existing leads)
    result = classify_lead(lead)

    if result["status"] == "spam":

        return problem("spam", result["reason"])
    if "prompt_injection_suspected" in result["flags"]:
        return problem("prompt_injection", result["reason"])
    if result["status"] == "needs_review":
        return problem("llm_failure", result["reason"])

    # 5. Duplicate of an existing lead: do not add, but watch for upgrades
    if lead["dup_status"] == "duplicate_existing":
        reason = f"Already in sheet as {lead['duplicate_of']} (tag: {lead['existing_tag']})."
        if result["tag"] == "Hot" and lead["existing_tag"] != "Hot":
            reason += f" New message looks Hot. Consider upgrading from {lead['existing_tag']}."
            outcome = notify_hot(lead, result, kind="upgrade",
                                 note=f"Existing lead {lead['duplicate_of']} is tagged {lead['existing_tag']}.")
            log.info("%s | notification: %s", lid, outcome)
        return problem("duplicate_existing", reason)

    # 6. Good new lead: add to sheet
    new_rows.append({
        "lead_id": f"L-{next_id}", "name": lead["name"], "email": lead["email"],
        "company": lead["company"], "source": "website", "tag": result["tag"],
        "created_at": lead["received_at"][:10], "draft_reply": result["reply"],
        "status": "new",
        "notes": " | ".join(lead["extra_messages"])})
    log.info("%s | added as L-%s | %s | via %s", lid, next_id, result["tag"], result["provider"])

    if result["tag"] == "Hot":
        outcome = notify_hot(lead, result)
        log.info("%s | notification: %s", lid, outcome)
    return True


def main():

    existing = load_existing(DATA / "existing_leads.csv")
    with open(DATA / "incoming_leads.json", encoding="utf-8") as f:
        incoming = json.load(f)
    raw_by_id = {r.get("id"): r for r in incoming}
    log.info("Loaded %d existing leads and %d incoming leads", len(existing), len(incoming))

    leads = check_duplicates([clean_lead(r) for r in incoming], existing)

    problems, new_rows = [], []
    next_id = max(int(r["lead_id"].split("-")[1]) for r in existing) + 1

    for lead in leads:
        try:
            if process_lead(lead, raw_by_id.get(lead["id"], {}), next_id, problems, new_rows) is True:
                next_id += 1
        except Exception as e:  # one bad lead must never stop the others
            log.exception("%s | unexpected error", lead.get("id"))
            problems.append({
                "received_id": lead.get("id", "?"), "name": lead.get("name", ""),
                "email": lead.get("email", ""), "company": lead.get("company", ""),
                "problem_type": "unexpected_error", "reason": f"{type(e).__name__}: {e}",
                "action_needed": ACTIONS["unexpected_error"],
                "original_submission": json.dumps(raw_by_id.get(lead.get("id"), {}), ensure_ascii=False)})

    write_final_sheet(existing, new_rows)
    write_problems(problems)

    counts = Counter(p["problem_type"] for p in problems)
    log.info("=" * 60)
    log.info("SUMMARY: %d received -> %d added to sheet, %d need attention",
             len(incoming), len(new_rows), len(problems))
    for ptype, n in counts.items():

        log.info("   %-20s %d", ptype, n)
    log.info("Files: output/leads_final.csv, output/problems.csv, output/notifications.log, output/run.log")


if __name__ == "__main__":
    main()