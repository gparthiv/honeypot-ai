from fastapi import FastAPI, Request, HTTPException
from google import genai
import os
import re
import requests

app = FastAPI()

# ========================
# Environment Keys
# ========================

API_KEY = os.getenv("API_KEY", "test@123")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

# ========================
# Gemini Client Setup
# ========================

client = genai.Client(api_key=GEMINI_KEY)
MODEL_NAME = "gemini-3-flash-preview"

# ========================
# Memory
# ========================

sessions = {}
session_meta = {}

# ========================
# Scam Detection
# ========================

def detect_scam(text: str):

    text = text.lower()

    score = 0
    keywords = []

    rules = {
        "urgency": (["urgent", "immediately", "now", "jaldi", "today"], 20),
        "threat": (["block", "blocked", "suspend", "police", "legal"], 25),
        "finance": (["bank", "upi", "account", "payment", "transfer"], 20),
        "verify": (["verify", "confirm", "otp", "share", "update"], 15),
        "impersonate": (["rbi", "officer", "department", "govt"], 20)
    }

    for _, (words, points) in rules.items():
        for word in words:
            if word in text:
                score += points
                keywords.append(word)

    confidence = min(score / 100, 1.0)

    return {
        "is_scam": score >= 50,
        "score": score,
        "confidence": round(confidence, 2),
        "keywords": list(set(keywords))
    }


# ========================
# Intelligence Extraction
# ========================

def extract_intelligence(text: str):

    intel = {
        "upiIds": [],
        "bankAccounts": [],
        "phoneNumbers": [],
        "phishingLinks": []
    }

    # UPI
    upi_pattern = r"[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}"
    upis = re.findall(upi_pattern, text)

    # Phones
    phone_pattern = r"(?:\+91|0)?[6-9]\d{9}"
    phones_raw = re.findall(phone_pattern, text)

    phones = []
    for p in phones_raw:
        digits = re.sub(r"\D", "", p)
        phones.append(digits[-10:])

    # URLs
    url_pattern = r"https?://[^\s]+"
    urls = re.findall(url_pattern, text)
    urls = [u.rstrip(".,)") for u in urls]

    # Bank
    bank_pattern = r"\b\d{9,18}\b"
    raw_accounts = re.findall(bank_pattern, text)

    accounts = []
    for acc in raw_accounts:
        if acc[-10:] not in phones:
            accounts.append(acc)

    intel["upiIds"] = list(set(upis))
    intel["phoneNumbers"] = list(set(phones_raw))
    intel["phishingLinks"] = list(set(urls))
    intel["bankAccounts"] = list(set(accounts))

    return intel


# ========================
# GUVI Callback
# ========================

GUVI_CALLBACK = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"


def send_to_guvi(session_id, history, intel, keywords):

    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": len(history),
        "extractedIntelligence": {
            "bankAccounts": intel["bankAccounts"],
            "upiIds": intel["upiIds"],
            "phishingLinks": intel["phishingLinks"],
            "phoneNumbers": intel["phoneNumbers"],
            "suspiciousKeywords": keywords
        },
        "agentNotes": "Automated honeypot detected scam and extracted intelligence"
    }

    try:
        r = requests.post(GUVI_CALLBACK, json=payload, timeout=5)
        print("GUVI CALLBACK:", r.status_code)

    except Exception as e:
        print("GUVI CALLBACK ERROR:", e)


# ========================
# Gemini Helper
# ========================

def ask_gemini(prompt: str) -> str:

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        text = response.text.strip()

        text = ''.join(c for c in text if c.isascii())
        text = text.replace("\n", " ")

        ban_words = [
            "salary", "rent", "mummy", "papa", "fees", "bp",
            "tension", "savings", "family", "bacha", "health"
        ]

        for w in ban_words:
            text = text.replace(w, "")

        text = text.split(".")[0].strip()

        return text[:100]

    except Exception as e:
        print("GEMINI ERROR:", e)
        return "Sorry, network issue. Please repeat."


# ========================
# API Endpoint
# ========================

@app.post("/honeypot")
async def honeypot(request: Request):

    key = request.headers.get("x-api-key")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    data = await request.json()

    session_id = data.get("sessionId", "default")
    message = data.get("message", {}).get("text", "").strip()

    detection = detect_scam(message)
    intelligence = extract_intelligence(message)

    history = sessions.get(session_id, [])
    history.append(f"Scammer: {message}")

    # Init meta
    if session_id not in session_meta:
        session_meta[session_id] = {
            "submitted": False,
            "intel": {
                "upiIds": [],
                "bankAccounts": [],
                "phoneNumbers": [],
                "phishingLinks": []
            }
        }

    meta = session_meta[session_id]

    for k in meta["intel"]:
        meta["intel"][k] = list(set(meta["intel"][k] + intelligence[k]))

    # Auto submit
    if detection["is_scam"] and len(history) >= 8 and not meta["submitted"]:

        send_to_guvi(
            session_id,
            history,
            meta["intel"],
            detection["keywords"]
        )

        meta["submitted"] = True

    prompt = f"""
You are pretending to be a normal Indian bank customer chatting on WhatsApp.

Rules:
- Max 2 short sentences
- No emojis
- No stories
- Sound confused
- Hinglish or English

Conversation:
{chr(10).join(history)}

Last: {message}

Reply:
"""

    reply = ask_gemini(prompt)

    history.append(f"You: {reply}")
    sessions[session_id] = history

    return {
        "status": "success",
        "reply": reply,
        "scamDetected": detection["is_scam"],
        "confidence": detection["confidence"],
        "keywords": detection["keywords"],
        "extractedIntelligence": intelligence
    }


# ========================
# Health
# ========================

@app.get("/")
def home():
    return {"message": "Honeypot running with Gemini AI"}
