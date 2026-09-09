#!/usr/bin/env python3
"""Register an NFC card after the PN532 prints its UID."""

from database import add_card

uid = input("Card UID (example AA:BB:CC:DD): ").strip().upper()
name = input("User name: ").strip()
if not uid or not name:
    raise SystemExit("UID and name are required.")
add_card(uid, name)
print(f"Registered {name} with UID {uid}.")
