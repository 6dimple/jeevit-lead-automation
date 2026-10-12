import json
import os
import urllib.request

# ---------------------------------------------------------------
# Each provider takes (system_prompt, user_prompt, lead) and returns
# a JSON *string*, exactly like a real LLM would.
# ---------------------------------------------------------------

HOT_WORDS = ["budget", "approved", "ready to go ahead", "send over a proposal",
             "this month", "start im", "get going"]
COLD_WORDS = ["just researching", "researching options", "next quarter"]
GERMAN_WORDS = ["wir ", "ist ", "suchen", "unsere", "budget ist"]


def stub_llm(system_prompt, user_prompt, lead):
    """STUB: simple keyword rules. NOT a real AI. Used when no API key is set."""
    text = lead["message"].lower()

    if any(w in text for w in HOT_WORDS):
        tag, reason = "Hot", "Mentions budget, timing or readiness to buy (keyword rule)."
    elif any(w in text for w in COLD_WORDS):
        tag, reason = "Cold", "Says they are only researching or timing is far off (keyword rule)."
    else:
        tag, reason = "Warm", "Shows interest but no clear budget or urgency (keyword rule)."

    first = lead["name"].split()[0] if lead["name"] else "there"
    if any(w in text for w in GERMAN_WORDS):
        reply = (f"Hallo {first}, vielen Dank für Ihre Nachricht. Gerne besprechen wir Ihre "
                 f"Anforderungen in einem kurzen Gespräch. Wann passt es Ihnen diese Woche?")
    else:
        reply = (f"Hi {first}, thanks for getting in touch. We'd be happy to talk through what "

                 f"you need. Do you have 20 minutes for a quick call this week?")
    return json.dumps({"tag": tag, "reason": reason, "reply": reply})


def gemini_llm(system_prompt, user_prompt, lead):
    """Real call to Google Gemini (free tier). Needs GEMINI_API_KEY."""
    key = os.environ["GEMINI_API_KEY"]
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")  # check Google AI Studio for current names
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["candidates"][0]["content"]["parts"][0]["text"]


def get_provider():
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini", gemini_llm
    return "stub", stub_llm