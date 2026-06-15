import os
from fastapi import Header, HTTPException
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("APP_API_KEY")


async def require_api_key(x_api_key: str = Header(...)):
    """FastAPI dependency — inject into any route to protect it."""
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured on server")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
