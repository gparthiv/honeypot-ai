"""
Enhanced Agentic Honeypot - India AI Impact Buildathon 2026
All Winning Features Integrated
"""

from fastapi import FastAPI, Request, HTTPException
from google import genai
import os
import re
import requests
import random
import asyncio
import time
from datetime import datetime

app = FastAPI(title="Enhanced Scam Honeypot")

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
# Memory & Session Data
# ========================
sessions = {}  # Conversation history
session_meta = {}  # Intelligence & metadata

# ========================
# 1. SMART REGIONAL LANGUAGE DETECTION
# ========================
def detect_user_region(text: str) -> str:
    """
    Detect user's region from FIRST message only
    User's region STAYS CONSISTENT - we don't adapt to scammer changes
    This maintains believability (Bengali person won't suddenly speak Tamil)
    """
    text_lower = text.lower()
    
    # Bengali indicators
    bengali_words = ['bhalo', 'accha', 'bujhlam', 'ki', 'keno', 'emon', 'korbo', 'bolchi']
    
    # Tamil indicators  
    tamil_words = ['enna', 'puriyala', 'seri', 'sollunga', 'nalla', 'ponga']
    
    # Telugu indicators
    telugu_words = ['enti', 'artham', 'kaale', 'chepandi', 'ela', 'sare']
    
    # Kannada indicators
    kannada_words = ['yenu', 'gottagilla', 'heli', 'chennagi', 'illa']
    
    # Malayalam indicators
    malayalam_words = ['enthu', 'manassilayilla', 'parayoo', 'nannaayi', 'alle']
    
    # Hindi/Hinglish (North India - most common)
    hindi_words = ['aap', 'kya', 'kaise', 'karo', 'theek', 'haan', 'nahi']
    
    # Check each region (order matters - check specific regions first)
    if any(word in text_lower for word in bengali_words):
        return "bengali"
    elif any(word in text_lower for word in tamil_words):
        return "tamil"
    elif any(word in text_lower for word in telugu_words):
        return "telugu"
    elif any(word in text_lower for word in kannada_words):
        return "kannada"
    elif any(word in text_lower for word in malayalam_words):
        return "malayalam"
    elif any(word in text_lower for word in hindi_words):
        return "north_indian"
    
    # Default to north Indian (most common for scams)
    return "north_indian"

def get_regional_style_guide(region: str) -> str:
    """
    Get consistent regional phrases based on USER'S region
    Doesn't change even if scammer uses different language
    """
    
    regional_guides = {
        "bengali": """
Use Bengali-English mix naturally:
- "Accha okay, but ki hoyeche?" (Okay, but what happened?)
- "Bujhlam na" (Didn't understand)  
- "Emon keno?" (Why like this?)
- "Bhalo kore bolo please" (Tell me properly please)
- "Ki korbo ekhon?" (What do I do now?)
""",
        
        "tamil": """
Use Tamil-English mix naturally:
- "Enna sir, puriyala" (What sir, don't understand)
- "Seri seri, but enna problem?" (Okay okay, but what problem?)
- "Nalla confusion-ah irukku" (Very confusing)
- "Sollunga sir" (Tell me sir)
""",
        
        "telugu": """
Use Telugu-English mix naturally:
- "Enti sir, artham kaale" (What sir, didn't understand)
- "Sare, kaani ela?" (Okay, but how?)
- "Chepandi clearly" (Tell clearly)
- "Enti ippudu?" (What now?)
""",
        
        "kannada": """
Use Kannada-English mix naturally:
- "Yenu sir, gottagilla" (What sir, don't know)
- "Heli properly" (Tell properly)
- "Chennagi explain maadi" (Explain well)
- "Yenu maadbekku?" (What should I do?)
""",
        
        "malayalam": """
Use Malayalam-English mix naturally:
- "Enthu sir, manassilayilla" (What sir, don't understand)
- "Parayoo clearly" (Tell clearly)
- "Nannaayi explain cheyyoo" (Explain well)
- "Enthu cheyyum?" (What to do?)
""",
        
        "north_indian": """
Use Hinglish naturally (Hindi-English mix):
- "Acha okay, but samajh nahi aa raha"
- "Kya karu ab?"
- "Theek hai sir, batao please"
- "Haan ji, sun raha hoon"
"""
    }
    
    return regional_guides.get(region, regional_guides["north_indian"])

def detect_language_style(text: str) -> str:
    """Detect English, Hinglish, or Hindi"""
    text_lower = text.lower()
    
    # Hindi/Hinglish indicators
    hindi_words = [
        'aap', 'hai', 'karo', 'jaldi', 'turant', 'nahi', 'haan',
        'kya', 'kaise', 'kyun', 'bhai', 'sir', 'madam', 'ji',
        'acha', 'theek', 'please', 'matlab', 'samajh', 'batao'
    ]
    
    # Regional words that also indicate non-English
    regional_words = [
        'bhalo', 'bujhlam', 'enna', 'puriyala', 'seri',
        'enti', 'artham', 'yenu', 'gottagilla', 'enthu'
    ]
    
    # Check for Devanagari script
    if any('\u0900' <= c <= '\u097F' for c in text):
        return "hindi"
    
    # Count mixed-language indicators
    mixed_count = sum(1 for word in hindi_words + regional_words if word in text_lower)
    
    if mixed_count >= 2:
        return "hinglish"
    elif any(word in text_lower for word in hindi_words + regional_words):
        return "hinglish"
    
    return "english"

# ========================
# 2. ENHANCED SCAM DETECTION
# ========================
def detect_scam_advanced(text: str):
    """Multi-pattern weighted scam detection"""
    text_lower = text.lower()
    
    # Weighted scoring system
    patterns = {
        'urgency': {
            'keywords': ['urgent', 'immediately', 'now', 'today', 'turant', 'jaldi', 'within', 'asap'],
            'weight': 25
        },
        'threats': {
            'keywords': ['block', 'blocked', 'suspend', 'close', 'legal', 'arrest', 'police', 'court', 'penalty', 'action'],
            'weight': 30
        },
        'financial': {
            'keywords': ['bank', 'account', 'upi', 'payment', 'transfer', 'credit', 'debit', 'card', 'money'],
            'weight': 20
        },
        'verification': {
            'keywords': ['verify', 'confirm', 'update', 'validate', 'share', 'provide', 'send', 'otp'],
            'weight': 20
        },
        'impersonation': {
            'keywords': ['rbi', 'reserve bank', 'government', 'police', 'officer', 'department', 'ministry', 'official'],
            'weight': 25
        }
    }
    
    score = 0
    detected_keywords = []
    matched_categories = []
    
    for category, data in patterns.items():
        category_matched = False
        for keyword in data['keywords']:
            if keyword in text_lower:
                if not category_matched:  # Count category only once
                    score += data['weight']
                    matched_categories.append(category)
                    category_matched = True
                detected_keywords.append(keyword)
    
    # Determine scam type
    scam_type = "unknown"
    if 'bank' in text_lower or 'account' in text_lower:
        scam_type = "bank_fraud"
    elif 'upi' in text_lower or 'payment' in text_lower:
        scam_type = "upi_scam"
    elif 'prize' in text_lower or 'won' in text_lower or 'lottery' in text_lower:
        scam_type = "prize_scam"
    elif 'kyc' in text_lower or 'verify' in text_lower:
        scam_type = "verification_scam"
    
    confidence = min(score / 100.0, 1.0)
    is_scam = confidence >= 0.6  # 60% threshold
    
    return {
        "is_scam": is_scam,
        "score": score,
        "confidence": round(confidence, 2),
        "keywords": list(set(detected_keywords)),
        "scam_type": scam_type,
        "categories": matched_categories
    }

# ========================
# 3. ENHANCED INTELLIGENCE EXTRACTION
# ========================
def extract_intelligence_advanced(text: str, existing_intel: dict) -> dict:
    """Enhanced extraction with deduplication"""
    
    # Bank accounts - multiple formats
    bank_patterns = [
        r'\b\d{11,18}\b',  # 9-18 digits
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4,10}\b',  # Formatted
    ]
    
    for pattern in bank_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            clean = re.sub(r'[-\s]', '', match)
            if 11 <= len(clean) <= 18 and clean not in existing_intel['bankAccounts']:
                existing_intel['bankAccounts'].append(clean)
    
    # UPI IDs
    upi_pattern = r'([a-zA-Z0-9.\-_]{2,}@(upi|paytm|ybl|apl|okaxis|oksbi|okicici|gpay))'

    matches = re.findall(upi_pattern, text, re.IGNORECASE)

    for full, provider in matches:
        upi = full.strip().lower()
        if upi not in existing_intel['upiIds']:
            existing_intel['upiIds'].append(upi)

    
    # Phone numbers - multiple formats
    phone_patterns = [
        r'\+91[-\s]?\d{10}',
        r'\b[6-9]\d{9}\b',
        r'\b0\d{10}\b'
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            clean = re.sub(r'[-\s]', '', match)
            if clean not in existing_intel['phoneNumbers']:
                existing_intel['phoneNumbers'].append(clean)
    
    # URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    for url in urls:
        url = url.rstrip('.,)')
        if url not in existing_intel['phishingLinks']:
            existing_intel['phishingLinks'].append(url)
    
    # Email addresses (for scammer contact)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    for email in emails:
        if email not in existing_intel.get('emailAddresses', []):
            if 'emailAddresses' not in existing_intel:
                existing_intel['emailAddresses'] = []
            existing_intel['emailAddresses'].append(email)
    
    # Names (basic detection - capitalized words)
    # Look for "My name is X" or "I am X from"
    name_patterns = [
    r'(?:my name is|i am|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
    r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:from|speaking|here)',
    r'(?:main|mai|main hoon|i am)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
    r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(?:rbi|bank|officer)'
    ]

    for pattern in name_patterns:
        names = re.findall(pattern, text, re.IGNORECASE)
        for name in names:
            if isinstance(name, tuple):
                name = name[0] if name[0] else name[1]
            name = name.strip()
            if len(name) > 2 and name not in existing_intel.get('scammerNames', []):
                if 'scammerNames' not in existing_intel:
                    existing_intel['scammerNames'] = []
                existing_intel['scammerNames'].append(name)
    
    # Addresses (basic detection - pincode based)
    pincode_pattern = r'\b[1-9]\d{5}\b'
    pincodes = re.findall(pincode_pattern, text)
    for pin in pincodes:
        if pin not in existing_intel.get('pincodes', []):
            if 'pincodes' not in existing_intel:
                existing_intel['pincodes'] = []
            existing_intel['pincodes'].append(pin)
    
    # IFSC codes
    ifsc_pattern = r'\b[A-Z]{4}0[A-Z0-9]{6}\b'
    ifsc_codes = re.findall(ifsc_pattern, text)
    for code in ifsc_codes:
        if code not in existing_intel.get('ifscCodes', []):
            if 'ifscCodes' not in existing_intel:
                existing_intel['ifscCodes'] = []
            existing_intel['ifscCodes'].append(code)
    
    # Store raw text snippets that might contain addresses or other info
    # This catches anything we might have missed
    if len(text) > 20:  # Only store substantial messages
        if 'rawMessages' not in existing_intel:
            existing_intel['rawMessages'] = []
        if text not in existing_intel['rawMessages']:
            existing_intel['rawMessages'].append(text[:200])  # First 200 chars
    
    return existing_intel

# ========================
# 4. DYNAMIC PERSONA GENERATION
# ========================
def generate_persona(scam_type: str, language_style: str, turn: int) -> str:
    """Generate persona based on scam type and stage"""
    
    # Base personas for each scam type
    personas = {
        "bank_fraud": {
            "english": "worried middle-aged bank customer, not tech-savvy, nervous about account",
            "hinglish": "worried Indian person, mix Hindi-English naturally, nervous",
            "hindi": "चिंतित भारतीय ग्राहक"
        },
        "upi_scam": {
            "english": "confused UPI user, worried about money",
            "hinglish": "UPI use karta hoon but confused, paisa ka tension",
            "hindi": "UPI उपयोगकर्ता"
        },
        "prize_scam": {
            "english": "excited but suspicious, wants to believe",
            "hinglish": "excited! Prize mila? But thoda suspicious",
            "hindi": "उत्साहित लेकिन सावधान"
        },
        "verification_scam": {
            "english": "willing to help but confused about process",
            "hinglish": "help karna chahta hoon but process samajh nahi aa raha",
            "hindi": "सहायता के लिए तैयार"
        }
    }
    
    persona = personas.get(scam_type, personas["bank_fraud"]).get(language_style, "confused person")
    
    # Stage-based instructions
    if turn <= 2:
        stage = "INITIAL: Show worry/confusion. Ask what's happening."
    elif turn <= 5:
        stage = "BUILDING TRUST: Show willingness. Ask clarifying questions."
    elif turn <= 10:
        stage = "EXTRACTING: Pretend to comply but need details. Ask for their account/number 'to verify'."
    else:
        stage = "FINAL: Show technical difficulties. Request alternative methods."
    
    return f"You are a {persona}. {stage}"

# ========================
# 5. ENHANCED GEMINI INTERACTION
# ========================
async def ask_gemini_enhanced(
    history: list,
    current_msg: str,
    scam_type: str,
    language_style: str,
    user_region: str,
    turn: int
) -> str:
    """Enhanced Gemini interaction with timeout + safe trimming"""

    persona = generate_persona(scam_type, language_style, turn)

    context = "\n".join(history[-6:]) if history else ""

    regional_style = get_regional_style_guide(user_region)

    prompt = f"""{persona}

{regional_style}

CRITICAL RULES:
- Maximum 2 sentences
- No emojis ever
- No dramatic stories
- Sound natural and confused
- Ask questions that might reveal scammer's details
- NEVER reveal you know it's a scam
- STICK TO YOUR REGION

TRICKING TACTICS:
- Ask them to confirm their number/account
- Say links are not working
- Ask where they are calling from
- Pretend to verify

CONVERSATION SO FAR:
{context}

SCAMMER JUST SAID: {current_msg}

Your confused response (1-2 sentences only):"""

    try:
        start = time.time()

        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model=MODEL_NAME,
                contents=prompt
            ),
            timeout=8
        )

        print("⏱️ Gemini time:", round(time.time() - start, 2), "sec")

        text = response.text.strip()

        # Keep ASCII + Devanagari
        text = ''.join(c for c in text if c.isascii() or '\u0900' <= c <= '\u097F')

        # Normalize spaces
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove banned words safely
        ban_words = [
            "salary", "rent", "mummy", "papa", "fees", "bp",
            "tension", "savings", "family", "bacha", "health",
            "income", "loan", "emi", "daughter", "son"
        ]

        for word in ban_words:
            text = re.sub(rf'\b{word}\b', '', text, flags=re.IGNORECASE)

        text = re.sub(r'\s+', ' ', text).strip()

        # Sentence-aware trimming
        parts = re.split(r'(?<=[.!?])\s+', text)

        text = " ".join(parts[:2]).strip()

        MAX_LEN = 150

        if len(text) > MAX_LEN:
            cut = text[:MAX_LEN]

            m = re.search(r'[.!?](?!.*[.!?])', cut)

            if m:
                text = cut[:m.end()]
            else:
                text = cut.rsplit(" ", 1)[0]

        # Add natural pauses (rare)
        if random.random() < 0.12:
            pauses = ["Ek minute... ", "Wait... ", "Hmm... "] \
                if language_style == "hinglish" else ["Let me think... ", "Wait... "]

            text = random.choice(pauses) + text

        if not text.endswith(('.', '?', '!')):
            text += random.choice(['.', '?'])

        return text if text else "Samajh nahi aa raha. Thoda clearly batao?"

    except Exception as e:
        print("❌ GEMINI ERROR:", e)

        fallbacks = {
    "english": [
        "I'm confused. Can you explain properly?",
        "Wait, I don't understand this.",
        "Can you send details again?",
        "This link is not opening for me."
    ],
    "hinglish": [
        "Samajh nahi aa raha, thoda clearly batao.",
        "Ruko, mujhe doubt ho raha hai.",
        "Ye process thoda confusing lag raha hai.",
        "Aap pehle apna number confirm karo."
    ],
    "hindi": [
        "समझ नहीं आ रहा, फिर से बताइए।",
        "यह लिंक काम नहीं कर रहा।"
    ]
}

    return random.choice(fallbacks.get(language_style, fallbacks["hinglish"]))




# ========================
# 6. GUVI CALLBACK
# ========================
GUVI_CALLBACK = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

def send_to_guvi(session_id: str, history: list, intel: dict, keywords: list, scam_type: str):
    """Send final results to GUVI"""
    
    # Generate agent notes
    intel_summary = []
    if intel.get("bankAccounts"):
        intel_summary.append(f"{len(intel['bankAccounts'])} bank accounts")
    if intel.get("upiIds"):
        intel_summary.append(f"{len(intel['upiIds'])} UPI IDs")
    if intel.get("phishingLinks"):
        intel_summary.append(f"{len(intel['phishingLinks'])} phishing links")
    if intel.get("phoneNumbers"):
        intel_summary.append(f"{len(intel['phoneNumbers'])} phone numbers")
    if intel.get("emailAddresses"):
        intel_summary.append(f"{len(intel['emailAddresses'])} emails")
    if intel.get("scammerNames"):
        intel_summary.append(f"{len(intel['scammerNames'])} names")
    
    summary = ", ".join(intel_summary) if intel_summary else "keywords only"
    
    # Prepare additional intelligence for agent notes
    extra_notes = []
    if intel.get("ifscCodes"):
        extra_notes.append(f"IFSC: {', '.join(intel['ifscCodes'])}")
    if intel.get("pincodes"):
        extra_notes.append(f"Pincodes: {', '.join(intel['pincodes'])}")
    
    notes = f"Scam type: {scam_type}. Extracted: {summary}. Turns: {len(history)//2}."
    if extra_notes:
        notes += " Additional: " + "; ".join(extra_notes)
    
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": len(history),
        "extractedIntelligence": {
            "bankAccounts": intel.get("bankAccounts", []),
            "upiIds": intel.get("upiIds", []),
            "phishingLinks": intel.get("phishingLinks", []),
            "phoneNumbers": intel.get("phoneNumbers", []),
            "suspiciousKeywords": keywords
        },
        "agentNotes": notes
    }
    
    try:
        r = requests.post(GUVI_CALLBACK, json=payload, timeout=10)
        print(f"✅ GUVI CALLBACK: {r.status_code} - Session: {session_id}")
        print(f"📊 Extracted: {summary}")
        if extra_notes:
            print(f"📌 Additional: {'; '.join(extra_notes)}")
        return True
    except Exception as e:
        print(f"❌ GUVI CALLBACK ERROR: {e}")
        return False

# ========================
# 7. MAIN API ENDPOINT
# ========================
@app.post("/honeypot")
async def honeypot(request: Request):
    """Enhanced honeypot endpoint with all features"""
    
    # Authentication
    key = request.headers.get("x-api-key")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # Parse request
    data = await request.json()
    session_id = data.get("sessionId", "default")
    message = data.get("message", {}).get("text", "").strip()
    
    if not message:
        raise HTTPException(status_code=400, detail="Empty message")
    
    incoming_history = data.get("conversationHistory", [])

    if incoming_history and session_id not in sessions:
        sessions[session_id] = [
            f"{m['sender'].capitalize()}: {m['text']}"
            for m in incoming_history
        ]
    
    # Detect language style
    language_style = detect_language_style(message)
    
    # Advanced scam detection
    detection = detect_scam_advanced(message)
    
    # Initialize session if new
    if session_id not in sessions:
        # Detect user's region from FIRST message (stays consistent)
        user_region = detect_user_region(message)
        
        sessions[session_id] = []
        session_meta[session_id] = {
            "submitted": False,
            "scam_detected": False,
            "scam_type": "unknown",
            "language_style": language_style,
            "user_region": user_region,  # SET ONCE, NEVER CHANGES
            "turn_count": 0,
            "intel": {
                "upiIds": [],
                "bankAccounts": [],
                "phoneNumbers": [],
                "phishingLinks": [],
                "emailAddresses": [],
                "scammerNames": [],
                "pincodes": [],
                "ifscCodes": [],
                "rawMessages": []
            },
            "keywords": []
        }
    
    meta = session_meta[session_id]
    meta["turn_count"] += 1
    meta["language_style"] = language_style
    
    # Update scam detection status
    if detection["is_scam"] and not meta["scam_detected"]:
        meta["scam_detected"] = True
        meta["scam_type"] = detection["scam_type"]
        print(f"🚨 Scam detected: {session_id} - Type: {detection['scam_type']} - Confidence: {detection['confidence']}")
    
    # Once scam, always scam (stability)
    if meta["scam_detected"]:
      detection["confidence"] = max(detection["confidence"], 0.7)
      detection["is_scam"] = True

    
    # Extract and accumulate intelligence
    current_intel = extract_intelligence_advanced(message, {
        "upiIds": [],
        "bankAccounts": [],
        "phoneNumbers": [],
        "phishingLinks": [],
        "emailAddresses": [],
        "scammerNames": [],
        "pincodes": [],
        "ifscCodes": [],
        "rawMessages": []
    })
    
    for key in meta["intel"]:
        meta["intel"][key] = list(set(meta["intel"][key] + current_intel[key]))
    
    # Accumulate keywords
    meta["keywords"] = list(set(meta["keywords"] + detection["keywords"]))
    
    # Add to conversation history
    history = sessions[session_id]
    history.append(f"Scammer: {message}")
    
    # Generate AI response with enhanced prompting
    reply = await ask_gemini_enhanced(
        history,
        message,
        meta["scam_type"],
        meta["language_style"],
        meta["user_region"],  # User's region (consistent throughout)
        meta["turn_count"]
    )
    
    history.append(f"You: {reply}")
    sessions[session_id] = history
    
    # Auto-submit to GUVI (after sufficient engagement)
    should_submit = (
        meta["scam_detected"] and
        meta["turn_count"] >= 8 and
        not meta["submitted"]
    )
    
    if should_submit:
        send_to_guvi(
            session_id,
            history,
            meta["intel"],
            meta["keywords"],
            meta["scam_type"]
        )
        meta["submitted"] = True
    
    # Return response
    return {
        "status": "success",
        "reply": reply,
        "scamDetected": detection["is_scam"],
        "confidence": detection["confidence"],
        "keywords": detection["keywords"],
        "extractedIntelligence": current_intel,
        "sessionTurns": meta["turn_count"],
        "languageDetected": language_style
    }

# ========================
# 8. HEALTH & STATUS ENDPOINTS
# ========================
@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Enhanced Agentic Honeypot",
        "version": "2.0",
        "features": [
            "Multi-pattern scam detection",
            "Adaptive Hinglish/English",
            "Dynamic persona system",
            "4-stage conversation strategy",
            "Human behavior simulation",
            "Advanced intelligence extraction"
        ],
        "active_sessions": len(sessions)
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(sessions),
        "model": MODEL_NAME
    }

@app.get("/stats")
def stats():
    """Statistics endpoint"""
    total_intel = {
        "upiIds": 0,
        "bankAccounts": 0,
        "phoneNumbers": 0,
        "phishingLinks": 0
    }
    
    scam_count = 0
    for meta in session_meta.values():
        if meta["scam_detected"]:
            scam_count += 1
        for key in total_intel:
            total_intel[key] += len(meta["intel"][key])
    
    return {
        "total_sessions": len(sessions),
        "scams_detected": scam_count,
        "total_intelligence": total_intel,
        "submitted_to_guvi": sum(1 for m in session_meta.values() if m["submitted"])
    }

# ========================
# Run
# ========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
