"""
Authentication API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
import traceback
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.user import User
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/auth", tags=["auth"])


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Normalize email and username to lowercase for consistency
    email_lower = user_data.email.lower().strip()
    username_lower = user_data.username.strip().lower()
    
    # Check if user exists (case-insensitive)
    db_user = db.query(User).filter(
        (User.email == email_lower) | (User.username == username_lower)
    ).first()
    
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=email_lower,
        username=username_lower,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    # Make username lookup case-insensitive
    username_lower = user_data.username.strip().lower()
    user = db.query(User).filter(User.username == username_lower).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login-form")
async def login_form(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login via form (for web interface)"""
    # Make username lookup case-insensitive
    username_lower = username.strip().lower()
    user = db.query(User).filter(User.username == username_lower).first()
    
    if not user:
        return RedirectResponse(
            url="/login?error=invalid_credentials",
            status_code=status.HTTP_302_FOUND
        )
    
    # Verify password
    if not verify_password(password, user.hashed_password):
        return RedirectResponse(
            url="/login?error=invalid_credentials",
            status_code=status.HTTP_302_FOUND
        )
    
    if not user.is_active:
        return RedirectResponse(
            url="/login?error=inactive_user",
            status_code=status.HTTP_302_FOUND
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    # Debug logging
    if settings.DEBUG:
        print(f"Login successful for user: {user.username} (ID: {user.id})")
        print(f"Token created: {access_token[:30]}...")
    
    # Create redirect response
    response = RedirectResponse(
        url="/portfolio/summary",
        status_code=status.HTTP_302_FOUND
    )
    
    # Set cookie with proper settings for localhost
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # False for localhost HTTP
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        domain=None  # Don't set domain for localhost
    )
    
    if settings.DEBUG:
        print(f"[+] Login successful for: {user.username}")
        print(f"[+] Token created and cookie set")
        print(f"[+] Redirecting to /portfolio/summary")
    
    return response


@router.post("/register-form")
async def register_form(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    full_name: Optional[str] = Form(default=None),
    db: Session = Depends(get_db)
):
    """Register via form (for web interface)"""
    try:
        # Validate passwords match
        if password != password_confirm:
            return RedirectResponse(
                url="/register?error=password_mismatch",
                status_code=status.HTTP_302_FOUND
            )
        
        # Validate password length
        if len(password) < 8:
            return RedirectResponse(
                url="/register?error=password_too_short",
                status_code=status.HTTP_302_FOUND
            )
        
        # Validate email format (basic check)
        if "@" not in email or "." not in email.split("@")[-1]:
            return RedirectResponse(
                url="/register?error=invalid_email",
                status_code=status.HTTP_302_FOUND
            )
        
        # Validate username (no spaces, minimum length)
        if len(username.strip()) < 3:
            return RedirectResponse(
                url="/register?error=username_too_short",
                status_code=status.HTTP_302_FOUND
            )
        
        if " " in username:
            return RedirectResponse(
                url="/register?error=username_invalid",
                status_code=status.HTTP_302_FOUND
            )
        
        # Check if user exists
        db_user = db.query(User).filter(
            (User.email == email.lower().strip()) | (User.username == username.strip().lower())
        ).first()
        
        if db_user:
            return RedirectResponse(
                url="/register?error=user_exists",
                status_code=status.HTTP_302_FOUND
            )
        
        # Create new user
        hashed_password = get_password_hash(password)
        clean_full_name = None
        if full_name:
            clean_full_name = full_name.strip()
            if not clean_full_name:
                clean_full_name = None
        
        db_user = User(
            email=email.lower().strip(),
            username=username.strip().lower(),
            hashed_password=hashed_password,
            full_name=clean_full_name or username.strip(),
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Auto-login after registration
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.id}, expires_delta=access_token_expires
        )
        
        # Debug logging
        if settings.DEBUG:
            print(f"Registration successful for user: {db_user.username} (ID: {db_user.id})")
            print(f"Token created: {access_token[:30]}...")
        
        response = RedirectResponse(url="/portfolio/summary", status_code=status.HTTP_302_FOUND)
        # Set cookie with proper settings (consistent with login-form)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # Set to False for localhost, True for HTTPS in production
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
            domain=None  # Don't set domain for localhost
        )
        
        if settings.DEBUG:
            print(f"[+] Registration successful for: {db_user.username}")
            print(f"[+] Token created and cookie set")
            print(f"[+] Redirecting to /portfolio/summary")
        
        return response
        
    except ValueError as e:
        # Validation errors
        try:
            db.rollback()
        except Exception:
            pass
        error_msg = str(e).replace(" ", "_")[:30]
        return RedirectResponse(
            url=f"/register?error=validation_error&msg={error_msg}",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        # Log the error with full traceback
        error_trace = traceback.format_exc()
        error_type = type(e).__name__
        error_message = str(e)
        print(f"\n{'='*60}")
        print(f"REGISTRATION ERROR: {error_type}")
        print(f"Message: {error_message}")
        print(f"{'='*60}")
        print(f"Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        try:
            db.rollback()
        except Exception:
            pass
        # Return error response with more details in debug mode
        if settings.DEBUG:
            error_msg = f"{error_type}: {error_message[:40]}"
        else:
            error_msg = "server_error"
        return RedirectResponse(
            url=f"/register?error={error_msg}",
            status_code=status.HTTP_302_FOUND
        )
