#!/usr/bin/env python3
"""Register an NFC card and its accessibility profile."""

from database import add_card

uid = input("Card UID (example AA:BB:CC:DD): ").strip().upper()
name = input("User name: ").strip()

if not uid or not name:
    raise SystemExit("UID and name are required.")

print("\nAccessibility profile:")
print("1. Pregnant")
print("2. Blind / low vision")
print("3. Deaf / hard of hearing")
print("4. Wheelchair user")
print("5. Mobility aid / crutches")
print("6. Other")
print("7. Multiple needs")

choice = input("Select 1-7: ").strip()
profiles = {
    "1": "Pregnant",
    "2": "Blind / low vision",
    "3": "Deaf / hard of hearing",
    "4": "Wheelchair user",
    "5": "Mobility aid / crutches",
}

if choice in profiles:
    accessibility = profiles[choice]
elif choice == "7":
    accessibility = input("Enter needs, separated by commas: ").strip()
elif choice == "6":
    accessibility = input("Enter accessibility need: ").strip()
else:
    raise SystemExit("Invalid profile selection.")

if not accessibility:
    raise SystemExit("Accessibility profile is required.")

add_card(uid, name, accessibility)
print(f"\nRegistered {name} with UID {uid}.")
print(f"Accessibility profile: {accessibility}")
