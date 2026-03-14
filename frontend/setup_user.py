"""
One-time user setup script for Edgewater Inventory Management System.
Run this once to create your superadmin account with a real bcrypt password.

Usage:
    cd frontend
    python setup_user.py

It will prompt you for a password, hash it, and insert the user + password
records into T_Users and T_Passwords via your existing DB connection.
"""

import sys
import getpass
from pathlib import Path
from datetime import datetime

# Add project paths (same as your Streamlit pages do)
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent / "rest"))

import bcrypt
from database import get_db_session
from models import Users, Passwords


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode(
        "utf-8"
    )


def main():
    email = "ianspraguesolberg@gmail.com"

    print(f"\n--- Edgewater User Setup ---")
    print(f"Email: {email}")
    print(f"Role:  Super Admin (superadmin)\n")

    password = getpass.getpass("Enter password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords don't match. Aborting.")
        return

    if len(password) < 8:
        print("Password must be at least 8 characters. Aborting.")
        return

    pw_hash = hash_password(password)

    try:
        with get_db_session() as session:
            # Check if user already exists
            existing = session.query(Users).filter(Users.Email == email).first()

            if existing:
                print(f"\nUser {email} already exists (UserID: {existing.UserID}).")
                update = input("Update password? (y/n): ").strip().lower()
                if update == "y":
                    pw_record = (
                        session.query(Passwords)
                        .filter(Passwords.UserID == existing.UserID)
                        .first()
                    )
                    if pw_record:
                        pw_record.PasswordHash = pw_hash
                        pw_record.LastPasswordChange = datetime.now()
                        pw_record.FailedLoginAttempts = 0
                        pw_record.AccountLockedUntil = None
                        pw_record.UpdatedAt = datetime.now()
                    else:
                        new_pw = Passwords(
                            UserID=existing.UserID,
                            PasswordHash=pw_hash,
                            LastPasswordChange=datetime.now(),
                            FailedLoginAttempts=0,
                            CreatedAt=datetime.now(),
                            UpdatedAt=datetime.now(),
                        )
                        session.add(new_pw)
                    session.commit()
                    print("Password updated.")
                else:
                    print("No changes made.")
                return

            # Create new user
            new_user = Users(
                Role="Admin",
                PermissionLevel="superadmin",
                Email=email,
                Active=1,
                CreatedAt=datetime.now(),
                UpdatedAt=datetime.now(),
            )
            session.add(new_user)
            session.flush()  # get the UserID

            new_pw = Passwords(
                UserID=new_user.UserID,
                PasswordHash=pw_hash,
                LastPasswordChange=datetime.now(),
                FailedLoginAttempts=0,
                CreatedAt=datetime.now(),
                UpdatedAt=datetime.now(),
            )
            session.add(new_pw)
            session.commit()

            print(f"\nCreated user:")
            print(f"  UserID: {new_user.UserID}")
            print(f"  Email:  {email}")
            print(f"  Role:   Admin (superadmin)")
            print(f"\nYou can now log in via the Streamlit app.")

    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
