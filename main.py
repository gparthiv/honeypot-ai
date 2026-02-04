from fastapi import FastAPI, Request, HTTPException
import os

app = FastAPI()

# Read API key from environment
API_KEY = os.getenv("API_KEY", "test123")


@app.post("/honeypot")
async def honeypot(request: Request):

    # Check API key
    key = request.headers.get("x-api-key")

    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        data = await request.json()
    except:
        data = {}

    return {
        "status": "success",
        "reply": "Service active"
    }


@app.get("/")
def home():
    return {"message": "Honeypot running"}

