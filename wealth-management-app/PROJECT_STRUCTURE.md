# Project Structure

```
wealth-management-app/
│
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   │
│   ├── api/                      # API routes
│   │   ├── __init__.py
│   │   ├── auth.py               # Authentication endpoints
│   │   ├── portfolio.py          # Portfolio management endpoints
│   │   ├── retirement.py         # Retirement planning endpoints
│   │   └── dependencies.py       # API dependencies (auth, etc.)
│   │
│   ├── core/                     # Core functionality
│   │   ├── config.py             # Application configuration
│   │   ├── database.py           # Database setup and session
│   │   ├── security.py           # Security utilities (hashing, JWT)
│   │   └── middleware.py         # Security middleware
│   │
│   ├── models/                   # Database models
│   │   ├── __init__.py
│   │   ├── user.py               # User model
│   │   ├── portfolio.py          # Portfolio, Asset, Liability, Insurance models
│   │   └── retirement.py         # Retirement plan model
│   │
│   └── services/                 # Business logic services
│       ├── __init__.py
│       ├── exchange_rate.py      # Currency exchange rate service
│       ├── portfolio_calculator.py  # Portfolio calculation logic
│       └── retirement_calculator.py # Retirement planning calculations
│
├── templates/                     # Jinja2 HTML templates
│   ├── base.html                 # Base template
│   ├── login.html                # Login page
│   ├── portfolio_summary.html    # Portfolio summary dashboard
│   ├── assets.html               # Assets management page
│   ├── liabilities.html          # Liabilities management page
│   └── retirement_plan.html      # Retirement planning page
│
├── static/                        # Static files
│   ├── css/
│   │   └── main.css              # Main stylesheet
│   └── js/
│       ├── main.js               # Common JavaScript utilities
│       ├── portfolio_summary.js  # Portfolio summary page logic
│       ├── assets.js             # Assets page logic
│       ├── liabilities.js        # Liabilities page logic
│       └── retirement_plan.js    # Retirement planning page logic
│
├── scripts/                       # Utility scripts
│   └── create_user.py            # Script to create users
│
├── config/                        # Configuration files (if needed)
├── migrations/                    # Database migrations (Alembic)
├── tests/                         # Test files
│
├── .env.example                   # Environment variables template
├── .env                           # Environment variables (not in git)
├── .gitignore                     # Git ignore rules
├── .dockerignore                  # Docker ignore rules
│
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker image definition
├── docker-compose.yml             # Docker Compose configuration
│
├── README.md                      # Main documentation
├── SETUP.md                       # Quick setup guide
├── PROJECT_STRUCTURE.md           # This file
│
├── start.bat                      # Windows startup script
├── start.sh                       # Linux/Mac startup script
└── run.py                         # Production runner

```

## Key Components

### Backend (FastAPI)
- **main.py**: Application entry point, route definitions, middleware setup
- **api/**: RESTful API endpoints for authentication, portfolio, and retirement planning
- **models/**: SQLAlchemy ORM models for database tables
- **services/**: Business logic for calculations and external API integrations
- **core/**: Configuration, database, security, and middleware

### Frontend (Jinja2 + JavaScript)
- **templates/**: HTML templates with Jinja2 templating
- **static/css/**: Stylesheets for modern UI
- **static/js/**: Client-side JavaScript for interactivity

### Database
- SQLite for development (default)
- PostgreSQL for production (configured in docker-compose.yml)

### Security
- JWT token-based authentication
- Bcrypt password hashing
- Security headers middleware
- CORS configuration
- Input validation with Pydantic

### Features
1. **Portfolio Management**
   - Track assets (stocks, mutual funds, real estate, etc.)
   - Track liabilities (loans, credit cards, etc.)
   - Track insurance policies
   - Multi-currency support (USD/INR)

2. **Retirement Planning**
   - Primary plan calculator (USD-denominated fields)
   - Secondary plan calculator (INR-denominated fields)
   - Combined planning view
   - Projection calculations

3. **Currency Conversion**
   - Live exchange rate API integration
   - Automatic currency conversion
   - Caching for performance

4. **Analytics**
   - Net worth calculation
   - Asset allocation visualization
   - Portfolio summary dashboard

## Database Schema

### Users
- User accounts with authentication

### Portfolios
- User portfolios (one-to-many with users)

### Assets
- Various asset types (stocks, mutual funds, real estate, etc.)
- Multi-currency support

### Liabilities
- Loans, credit cards, etc.
- Interest rates and due dates

### Insurance
- Insurance policies with coverage amounts

### Retirement Plans
- Primary and secondary scenario fields (USD / INR columns in the model)
- Calculation parameters

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (JSON)
- `POST /api/auth/login-form` - Login (Form)

### Portfolio
- `GET /api/portfolio/summary` - Portfolio summary
- `GET /api/portfolio/assets` - List assets
- `POST /api/portfolio/assets` - Create asset
- `GET /api/portfolio/liabilities` - List liabilities
- `POST /api/portfolio/liabilities` - Create liability
- `GET /api/portfolio/exchange-rate` - Get exchange rate

### Retirement
- `GET /api/retirement/plans` - List plans
- `POST /api/retirement/plans` - Create plan
- `GET /api/retirement/plans/{id}/calculate` - Calculate plan

## Web Pages

- `/` - Redirects to login
- `/login` - Login page
- `/portfolio/summary` - Portfolio summary dashboard
- `/portfolio/assets` - Assets management
- `/portfolio/liabilities` - Liabilities management
- `/plan` - Retirement planning
