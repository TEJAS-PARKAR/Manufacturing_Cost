"""
One-off script to seed initial users into MongoDB.
Run locally:  python seed_users.py
Safe to re-run: skips users that already exist.
"""
from backend.services.user_service import UserService

# --- EDIT THESE before running ---
USERS_TO_CREATE = [
    # username (==employee_id for suppliers), password, role
    ("EMP1002", "lol", "supplier"),
    ("TATA_ADMIN2", "lol", "tata"),
]


def main() -> None:
    service = UserService()
    if service.collection is None:
        raise SystemExit("❌ MongoDB not connected. Check your .env MONGODB_URI.")

    for username, password, role in USERS_TO_CREATE:
        try:
            service.register_user(username, password, role)
            print(f"✅ Created {role} user: {username}")
        except ValueError as exc:
            print(f"⏭️  Skipped {username}: {exc}")


if __name__ == "__main__":
    main()
