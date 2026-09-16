"""
setup_vapi.py — Automatically creates/updates the Vapi assistant and assigns the phone number.

Usage:
    python agent/setup_vapi.py

What it does:
    1. Reads vapi_assistant_config.json
    2. Substitutes {{API_BASE_URL}} with your deployed URL from .env
    3. Creates (or updates) the assistant via Vapi API
    4. Assigns the Vapi phone number to the assistant
    5. Prints the assistant ID and confirmation

Run this AFTER:
    - Deploying to Railway and having a live API_BASE_URL
    - Setting all env vars in .env

You can re-run it safely — if an assistant with the same name exists, it will update it.
"""

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
VAPI_PRIVATE_KEY = os.getenv("VAPI_PRIVATE_KEY")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID", "95990ced-27a5-475c-85c6-d402288bc30a")
API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")

VAPI_BASE = "https://api.vapi.ai"
HEADERS = {
    "Authorization": f"Bearer {VAPI_PRIVATE_KEY}",
    "Content-Type": "application/json",
}

CONFIG_FILE = Path(__file__).parent / "vapi_assistant_config.json"


def validate_env():
    """Check required env vars before making any API calls."""
    missing = []
    if not VAPI_PRIVATE_KEY:
        missing.append("VAPI_PRIVATE_KEY")
    if not API_BASE_URL:
        missing.append("API_BASE_URL (deploy to Railway first, then set this)")
    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        print("   Fill in .env and run again.")
        sys.exit(1)
    print(f"✅ Using API_BASE_URL: {API_BASE_URL}")


def load_config() -> dict:
    """Load and preprocess the Vapi assistant config JSON."""
    with open(CONFIG_FILE) as f:
        raw = f.read()

    # Substitute placeholder URL
    raw = raw.replace("{{API_BASE_URL}}", API_BASE_URL)

    config = json.loads(raw)
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key and config.get("model", {}).get("provider") == "groq":
        config["model"]["apiKey"] = groq_api_key

    print(f"✅ Loaded config: {CONFIG_FILE.name}")
    return config


def get_existing_assistant(name: str) -> str | None:
    """Check if an assistant with this name already exists. Returns ID or None."""
    resp = httpx.get(f"{VAPI_BASE}/assistant", headers=HEADERS)
    resp.raise_for_status()
    assistants = resp.json()
    for a in assistants:
        if a.get("name") == name:
            return a["id"]
    return None


def create_or_update_assistant(config: dict) -> str:
    """Create a new assistant or update the existing one. Returns assistant ID."""
    name = config.get("name", "Patient Registration Agent")
    existing_id = get_existing_assistant(name)

    if existing_id:
        print(f"🔄 Updating existing assistant: {name} (id: {existing_id})")
        resp = httpx.patch(
            f"{VAPI_BASE}/assistant/{existing_id}",
            headers=HEADERS,
            json=config,
        )
    else:
        print(f"➕ Creating new assistant: {name}")
        resp = httpx.post(
            f"{VAPI_BASE}/assistant",
            headers=HEADERS,
            json=config,
        )

    if resp.status_code not in (200, 201):
        print(f"❌ Vapi API error {resp.status_code}: {resp.text}")
        sys.exit(1)

    assistant_id = resp.json()["id"]
    print(f"✅ Assistant ready — ID: {assistant_id}")
    return assistant_id


def assign_phone_number(assistant_id: str):
    """Assign the provisioned Vapi phone number to this assistant."""
    print(f"📞 Assigning phone number {VAPI_PHONE_NUMBER_ID} → assistant {assistant_id}")

    resp = httpx.patch(
        f"{VAPI_BASE}/phone-number/{VAPI_PHONE_NUMBER_ID}",
        headers=HEADERS,
        json={"assistantId": assistant_id},
    )

    if resp.status_code not in (200, 201):
        print(f"❌ Phone assignment error {resp.status_code}: {resp.text}")
        print("   You may need to assign it manually in the Vapi dashboard.")
        return

    number_info = resp.json()
    phone = number_info.get("number", "+13854069126")
    print(f"✅ Phone number {phone} now routes to assistant: {assistant_id}")


def verify_setup():
    """Quick verification — fetch the assistant and confirm it looks right."""
    resp = httpx.get(f"{VAPI_BASE}/phone-number/{VAPI_PHONE_NUMBER_ID}", headers=HEADERS)
    if resp.status_code == 200:
        info = resp.json()
        assigned = info.get("assistantId", "NONE")
        number = info.get("number", "unknown")
        print(f"\n{'='*50}")
        print(f"✅ SETUP COMPLETE")
        print(f"   Phone Number : {number}")
        print(f"   Assistant ID : {assigned}")
        print(f"   API Base URL : {API_BASE_URL}")
        print(f"{'='*50}")
        print(f"\n📲 Call {number} to test your agent!")
        print(f"🔍 View records: {API_BASE_URL}/patients")
        print(f"📖 API docs:     {API_BASE_URL}/docs")
    else:
        print("⚠️  Could not verify setup — check Vapi dashboard manually")


if __name__ == "__main__":
    print("\n🚀 Vapi Assistant Setup Script")
    print("=" * 50)

    validate_env()
    config = load_config()
    assistant_id = create_or_update_assistant(config)
    assign_phone_number(assistant_id)
    verify_setup()
