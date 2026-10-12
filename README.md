# Lead Automation Workflow

Takes new website form submissions, cleans them, removes duplicates, tags each lead
Hot / Warm / Cold, drafts a first reply, writes the result to a sheet, notifies on Hot
leads, and records every problem with a reason.

**Stack:** Python 3 (standard library only, no installs needed).
**"Sheet":** CSV files (`output/leads_final.csv`), which can be imported into Google Sheets.
**LLM:** [Stub by default / Google Gemini when GEMINI_API_KEY is set]. See "LLM" below.

## How to run

```
py main.py or python main.py
```

Needs Python 3.8+. Reads `data/existing_leads.csv` and `data/incoming_leads.json`
(each of the 15 submissions is processed as if it arrived on a webhook) and writes to `output/`:

| File | Contents |
|---|---|
| `leads_final.csv` | Existing 12 leads + new leads, with tag, draft reply, status |
| `problems.csv` | Every lead NOT added, with the reason, a suggested action and the original submission |
| `notifications.log` | Hot-lead alerts |
| `run.log` | Full run log and summary |

Optional: set `GEMINI_API_KEY` to use a real LLM, and `SLACK_WEBHOOK_URL` for Slack alerts.

## Pipeline

1. **Clean** (`leads_clean.py`): trim and collapse spaces, lowercase emails, normalise names
   (`"  JAMES   o'CONNOR "` becomes `James O'Connor`), validate email format, handle missing fields.
2. **Deduplicate** (`dedupe.py`): compare against existing leads and earlier leads in the same batch.
   The match key is the lowercase email with any `+tag` removed.
3. **Classify** (`classify.py`, `llm.py`): spam and prompt-injection checks run first, then the LLM
   returns JSON (`tag`, `reason`, `reply`), which is validated.
4. **Write** (`output_writer.py`): new leads get IDs continuing from L-1013.
5. **Notify** (`notify.py`): Hot leads are logged, and sent to Slack if configured.
6. **Problems**: every lead lands in exactly one place, the sheet or `problems.csv`.

## Results on the sample data

15 received: **4 added** (Hannah Brooks, James O'Connor, Zoë Müller, Chloe Martin),
**11 flagged** in `problems.csv`:

| Lead | Problem |
|---|---|
| S-02, S-03, S-15 | Duplicate of existing leads |
| S-14 | Duplicate of S-12 in the same batch (extra message merged into S-12's notes) |
| S-04, S-05 | Missing email |
| S-06, S-07 | Invalid email |
| S-10 | Prompt-injection attempt |
| S-11 | Spam |
| S-13 | Empty message |

Hot leads notified: Hannah Brooks (S-01), Zoë Müller (S-09), and Tom Walsh (S-15, an existing
Warm lead whose new message looks Hot).

## LLM

The prompt is in `classify.py` (`SYSTEM_PROMPT`). It defines the three tags, requires JSON-only
output, requires the reply to be in the lead's language, forbids promising prices or discounts,
and tells the model that the lead message is untrusted data.

[**This submission was run with the keyword-rule STUB** (`stub_llm` in `llm.py`), not a real AI.
Results show `via stub` in the logs. A real call to Google Gemini is implemented in
`gemini_llm` but was [not tested / tested on date].]

## Assumptions

- Email is the identity of a lead. `tom+automation@x.com` and `tom@x.com` are the same person.
- A duplicate of an existing lead does not get a new row. If the new message looks Hot while the
  existing lead is not, a notification is sent suggesting an upgrade. Existing rows are never
  edited automatically.
- Leads with no valid email are not added to the sheet, because they can't be deduplicated.
  They go to `problems.csv` with the original submission so a human can follow up.
- Leads with an empty message are not tagged (nothing to judge).
- `source` is set to `website` and `created_at` to the date received.

## What happens when something fails

- **One lead breaks:** each lead runs in its own try/except. It is logged as `unexpected_error` in
  `problems.csv` and the rest continue.
- **LLM output is invalid or the call fails:** one retry, then the lead goes to `problems.csv`
  as `llm_failure`.
- **Prompt injection or spam:** detected in code before the LLM. Injection leads never get an
  automated reply. Spam doesn't use an LLM call.
- **Slack is down or unconfigured:** the alert is still written to `notifications.log`.

## Known limitations

- Spam and injection detection is pattern-based. It catches obvious cases, not clever ones.
- Duplicates are matched by email only (the same person with two emails would be missed).
- CSV output instead of Google Sheets. It is not triggered by a real webhook.
- Stub tagging is keyword-based. Slack sending is built but [untested].

## What I'd do next

1. Receive leads through a real webhook (FastAPI or n8n) instead of reading a file.
2. Write to Google Sheets through the API, with upserts and a "needs review" tab.
3. Fuzzy-match on name + company, and update existing leads instead of only flagging them.
4. Add proper unit tests and an evaluation set of labelled leads to measure LLM accuracy.
5. Retry with backoff and a queue for failed leads, plus an alert when the problem rate is high.
6. Send the draft reply as an email draft for human approval before it goes out.