"""
Test login functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password, create_access_token, decode_access_token
from datetime import timedelta

def test_login(username: str, password: str):
    """Test login flow"""
    db = SessionLocal()
    try:
        print(f"Testing login for: {username}")
        print("-" * 50)
        
        # Step 1: Find user
        username_lower = username.strip().lower()
        user = db.query(User).filter(User.username == username_lower).first()
        
        if not user:
            print(f"✗ User '{username}' not found!")
            return False
        
        print(f"✓ User found: {user.username} (ID: {user.id}, Active: {user.is_active})")
        
        # Step 2: Verify password
        if not verify_password(password, user.hashed_password):
            print("✗ Password verification failed!")
            return False
        
        print("✓ Password verified successfully")
        
        # Step 3: Create token
        token = create_access_token(
            data={"sub": user.id},
            expires_delta=timedelta(minutes=30)
        )
        print(f"✓ Token created: {token[:50]}...")
        
        # Step 4: Decode token
        decoded = decode_access_token(token)
        if not decoded:
            print("✗ Token decode failed!")
            return False
        
        print(f"✓ Token decoded successfully")
        print(f"  - User ID from token: {decoded.get('sub')}")
        print(f"  - Expires: {decoded.get('exp')}")
        
        # Step 5: Verify user can be loaded
        user_id = decoded.get("sub")
        if user_id:
            try:
                user_id = int(user_id)
                loaded_user = db.query(User).filter(User.id == user_id).first()
                if loaded_user and loaded_user.is_active:
                    print(f"✓ User loaded from token: {loaded_user.username}")
                    print("\n✓✓✓ LOGIN FLOW TEST PASSED ✓✓✓")
                    return True
                else:
                    print("✗ User not found or inactive")
                    return False
            except (ValueError, TypeError) as e:
                print(f"✗ Invalid user_id: {e}")
                return False
        
        return False
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import getpass
    
    print("Test Login Flow")
    print("=" * 50)
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    
    test_login(username, password)
