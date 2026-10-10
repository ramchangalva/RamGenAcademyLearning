# Quick Setup Guide

## Windows Setup (Recommended)

1. **Run the startup script**:
   ```cmd
   start.bat
   ```
   This will:
   - Create a virtual environment
   - Install dependencies
   - Create .env file
   - Initialize database
   - Start the server

2. **Create your first user**:
   ```cmd
   python scripts\create_user.py
   ```

3. **Access the application**:
   - Open browser: http://localhost:9000
   - Login with your credentials

## Manual Setup

### Step 1: Create Virtual Environment
```cmd
python -m venv venv
venv\Scripts\activate
```

### Step 2: Install Dependencies
```cmd
pip install -r requirements.txt
```

### Step 3: Configure Environment
```cmd
copy .env.example .env
```
Edit `.env` and set:
- `SECRET_KEY`: Generate a strong secret key (minimum 32 characters)
  - You can generate one using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### Step 4: Initialize Database
```cmd
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### Step 5: Create User
```cmd
python scripts\create_user.py
```

### Step 6: Run Application
```cmd
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

## First Steps After Setup

1. **Login** to the application
2. **Add Assets**: Go to Portfolio > Assets and add your assets
3. **Add Liabilities**: Go to Portfolio > Liabilities and add your liabilities
4. **Create Retirement Plan**: Go to Plan and create your retirement plan
5. **View Summary**: Check Portfolio > Summary to see your net worth

## Production Deployment

### Using Docker
```cmd
docker-compose up -d
```

### Manual Production
1. Set `ENVIRONMENT=production` in `.env`
2. Set `DEBUG=false` in `.env`
3. Use PostgreSQL instead of SQLite
4. Set up reverse proxy (nginx) for HTTPS
5. Run with multiple workers:
   ```cmd
   uvicorn app.main:app --host 0.0.0.0 --port 9000 --workers 4
   ```

## Troubleshooting

### Port Already in Use
Change the port in `start.bat` or run:
```cmd
uvicorn app.main:app --reload --host 0.0.0.0 --port 9001
```

### Database Errors
- Delete `wealth_management.db` and reinitialize
- Check database permissions

### Exchange Rate API Issues
- Check internet connection
- Application will use fallback rates if API fails

## Security Notes

- **Never commit `.env` file** to version control
- **Change `SECRET_KEY`** in production
- **Use HTTPS** in production (set up reverse proxy)
- **Use strong passwords** for database
- **Regular backups** of database
