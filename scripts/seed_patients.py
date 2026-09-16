"""
seed_patients.py — Insert 2 test patients into the deployed API.

Usage:
    python scripts/seed_patients.py

Run this AFTER the API is deployed and API_BASE_URL is set in .env.
These are fictional test patients — do not use real personal data.
"""

import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

TEST_PATIENTS = [
    {
        "first_name": "Jane",
        "last_name": "Smith",
        "date_of_birth": "1985-03-12",
        "sex": "female",
        "phone_number": "5550001001",
        "address_line_1": "42 Maple Street",
        "address_line_2": "Apt 3B",
        "city": "Boston",
        "state": "MA",
        "zip_code": "02101",
        "email": "jane.smith.test@example.com",
        "preferred_language": "English",
        "emergency_contact_name": "John Smith",
        "emergency_contact_phone": "5550001002",
    },
    {
        "first_name": "Robert",
        "last_name": "Garcia",
        "date_of_birth": "1972-11-28",
        "sex": "male",
        "phone_number": "5550002001",
        "address_line_1": "117 Oak Avenue",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60601",
        "insurance_provider": "BlueCross BlueShield",
        "insurance_member_id": "BCBS-2024-RG117",
        "preferred_language": "English",
    },
]


def seed():
    print(f"\n🌱 Seeding test patients to: {API_BASE_URL}")
    print("=" * 50)

    for patient in TEST_PATIENTS:
        try:
            resp = httpx.post(f"{API_BASE_URL}/patients", json=patient, timeout=15)
            if resp.status_code == 201:
                data = resp.json()["data"]
                print(f"✅ Created: {data['first_name']} {data['last_name']} → ID: {data['patient_id']}")
            elif resp.status_code == 422:
                print(f"⚠️  Validation error for {patient['first_name']}: {resp.json()}")
            else:
                print(f"❌ Error {resp.status_code} for {patient['first_name']}: {resp.text}")
        except httpx.ConnectError:
            print(f"❌ Cannot connect to {API_BASE_URL} — is the API running?")
            sys.exit(1)

    print("\n✅ Seeding complete!")
    print(f"🔍 View all patients: {API_BASE_URL}/patients")
    print(f"📖 API docs: {API_BASE_URL}/docs\n")


if __name__ == "__main__":
    seed()
