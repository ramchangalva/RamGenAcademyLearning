"""
Script to create a default user for the application
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User

def create_user(username: str, email: str, password: str, full_name: str = None):
    """Create a new user"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Normalize email and username to lowercase for consistency
        email_lower = email.lower().strip()
        username_lower = username.strip().lower()
        
        # Check if user exists (case-insensitive)
        existing_user = db.query(User).filter(
            (User.username == username_lower) | (User.email == email_lower)
        ).first()
        
        if existing_user:
            print(f"User with username '{username}' or email '{email}' already exists!")
            return False
        
        # Create new user
        hashed_password = get_password_hash(password)
        user = User(
            username=username_lower,
            email=email_lower,
            hashed_password=hashed_password,
            full_name=full_name or username,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"User '{username}' created successfully!")
        print(f"User ID: {user.id}")
        return True
        
    except Exception as e:
        print(f"Error creating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import getpass
    
    print("Create a new user for Wealth Management App")
    print("=" * 50)
    
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    full_name = input("Full Name (optional): ").strip() or None
    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm Password: ")
    
    if password != password_confirm:
        print("Passwords do not match!")
        sys.exit(1)
    
    if len(password) < 8:
        print("Password must be at least 8 characters long!")
        sys.exit(1)
    
    create_user(username, email, password, full_name)
