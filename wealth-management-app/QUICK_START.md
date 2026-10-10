# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Run Setup Script
```cmd
start.bat
```

### Step 2: Create Your User
```cmd
python scripts\create_user.py
```

### Step 3: Open Browser
Navigate to: **http://localhost:9000**

## 📋 Common Tasks

### Add Your First Asset
1. Login to the application
2. Go to **Portfolio > Assets**
3. Click **"Add Asset"**
4. Fill in the form (e.g., Stocks, Real Estate)
5. Save

### Add a Liability
1. Go to **Portfolio > Liabilities**
2. Click **"Add Liability"**
3. Enter loan or credit card details
4. Save

### Create Retirement Plan
1. Go to **Plan**
2. Click **"Create Plan"**
3. Fill in primary (USD) and/or secondary (INR) retirement details
4. Click **"Calculate"** to see projections

### View Portfolio Summary
1. Go to **Portfolio > Summary**
2. See your net worth, asset allocation, and more
3. Switch between USD and INR using the currency selector

## 💡 Tips

- **Currency Conversion**: The app automatically converts between USD and INR using live exchange rates
- **Asset Allocation**: View your asset distribution in the Portfolio Summary
- **Retirement Planning**: Model primary and alternate-currency scenarios
- **Data Entry**: Start with your largest assets and liabilities first

## 🔧 Troubleshooting

**Can't login?**
- Make sure you created a user with `python scripts\create_user.py`

**Portfolio shows zero?**
- Add assets and liabilities first
- Go to Portfolio > Assets and Portfolio > Liabilities

**Exchange rate not updating?**
- Check internet connection
- App will use fallback rates if API is unavailable

**Database errors?**
- Delete `wealth_management.db` and restart
- The database will be recreated automatically

## 📞 Need Help?

- Check `README.md` for detailed documentation
- Check `SETUP.md` for installation help
- Check `PROJECT_STRUCTURE.md` for code structure

## 🔒 Security Reminders

- Change `SECRET_KEY` in `.env` for production
- Use strong passwords
- Never commit `.env` file
- Use HTTPS in production
