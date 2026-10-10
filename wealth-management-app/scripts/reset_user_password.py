"""
Script to reset a user's password
"""
import sys
import os
import getpass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User

def reset_password(username: str, new_password: str):
    """Reset a user's password"""
    db = SessionLocal()
    
    try:
        # Find user (case-insensitive)
        user = db.query(User).filter(User.username == username.lower().strip()).first()
        
        if not user:
            print(f"User '{username}' not found!")
            return False
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        
        print(f"Password reset successfully for user: {user.username}")
        return True
        
    except Exception as e:
        print(f"Error resetting password: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("Reset User Password")
    print("=" * 50)
    
    username = input("Username: ").strip()
    new_password = getpass.getpass("New Password: ")
    confirm_password = getpass.getpass("Confirm Password: ")
    
    if new_password != confirm_password:
        print("Passwords do not match!")
        sys.exit(1)
    
    if len(new_password) < 8:
        print("Password must be at least 8 characters long!")
        sys.exit(1)
    
    reset_password(username, new_password)
