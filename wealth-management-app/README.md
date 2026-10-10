# Wealth Management Planning Application

A comprehensive wealth management and retirement planning application built with FastAPI, Jinja2, and modern web technologies. Use it to manage your portfolio, track assets and liabilities, and plan retirement—with multi-currency support suitable for users anywhere.

## Features

- **Portfolio Management**: Track assets, liabilities, and insurance in multiple currencies (e.g. USD and INR)
- **Live Exchange Rates**: Automatic currency conversion using live exchange rate APIs
- **Retirement Planning**: Model a primary plan and an alternate scenario in different currencies
- **Asset Allocation**: Visual representation of asset distribution
- **Secure Authentication**: JWT-based authentication with password hashing
- **Modern UI**: Clean, responsive interface matching professional wealth management dashboards

## Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Jinja2 Templates, Vanilla JavaScript
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT tokens with bcrypt password hashing
- **Charts**: Chart.js for data visualization

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- PostgreSQL (for production) or SQLite (for development)

### Local Development Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd wealth-management-app
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Create environment file**:
   ```bash
   copy .env.example .env
   ```
   Edit `.env` and set your `SECRET_KEY` (minimum 32 characters for production)

6. **Initialize the database**:
   ```bash
   python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

7. **Create a default user** (optional):
   ```bash
   python scripts/create_user.py
   ```

8. **Run the application**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
   ```

9. **Access the application**:
   Open your browser and navigate to `http://localhost:9000`

## Production Deployment

### Using Docker (Recommended)

**PostgreSQL (default `docker-compose.yml`)**

1. Create a `.env` file in the project root (Compose reads it for variable substitution). Copy from `.env.example` and set at least:
   - `SECRET_KEY` — strong random string, 32+ characters
   - `POSTGRES_PASSWORD` — database password (must match what you expect; default in compose is `wealthpass` if unset)

2. Build and start:
   ```bash
   docker compose up -d --build
   ```

3. Open `http://localhost:9000` (or set `WEB_PORT` in `.env` to map a different host port).

**SQLite (single container, `docker-compose.sqlite.yml`)**

```bash
# Set SECRET_KEY in .env first
docker compose -f docker-compose.sqlite.yml up -d --build
```

The database file is stored in the Docker volume `wealth_sqlite` at `/data/wealth_management.db` inside the container.

**Image name:** builds as **`wealthplanner:latest`** by default (`docker compose build` tags the `web` service that way).

**Push to Docker Hub (or another registry)**

Unqualified `docker push wealthplanner` targets `docker.io/library/wealthplanner`, which you cannot publish. Tag with your namespace, then push:

```bash
docker compose build web
docker tag wealthplanner:latest YOUR_DOCKERHUB_USER/wealthplanner:latest
docker login
docker push YOUR_DOCKERHUB_USER/wealthplanner:latest
```

Or set in `.env`: `DOCKER_IMAGE=YOUR_DOCKERHUB_USER/wealthplanner:latest` and run `docker compose build web` — the image will be tagged for push directly.

**Plain image (no Compose)**

```bash
docker build -t wealthplanner:latest .
docker run --rm -p 9000:9000 -e SECRET_KEY="your-32-plus-char-secret-key-here" wealthplanner:latest
```

Optional: `OPENAI_API_KEY`, `EXCHANGE_RATE_API_KEY`, `TRADING_SYNC_HMAC_SECRET` — pass with `-e` or via `.env` when using Compose.

### Manual Production Setup

1. **Install production dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL database**:
   ```sql
   CREATE DATABASE wealthdb;
   CREATE USER wealthuser WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE wealthdb TO wealthuser;
   ```

3. **Configure environment variables**:
   ```bash
   export SECRET_KEY="your-very-secure-secret-key-min-32-chars"
   export DATABASE_URL="postgresql://wealthuser:your_secure_password@localhost/wealthdb"
   export ENVIRONMENT="production"
   export DEBUG="false"
   ```

4. **Run database migrations** (if using Alembic):
   ```bash
   alembic upgrade head
   ```

5. **Run with production server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 9000 --workers 4
   ```

## Security Features

- **Password Hashing**: Bcrypt with configurable rounds
- **JWT Authentication**: Secure token-based authentication
- **HTTPS Ready**: Configure reverse proxy (nginx) for HTTPS in production
- **CSRF Protection**: Ready for CSRF token implementation
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **Input Validation**: Pydantic models for request validation

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user (JSON)
- `POST /api/auth/login-form` - Login user (Form)

### Portfolio
- `GET /api/portfolio/summary` - Get portfolio summary
- `GET /api/portfolio/assets` - Get all assets
- `POST /api/portfolio/assets` - Create new asset
- `GET /api/portfolio/liabilities` - Get all liabilities
- `POST /api/portfolio/liabilities` - Create new liability
- `GET /api/portfolio/exchange-rate` - Get current exchange rate

### Retirement Planning
- `GET /api/retirement/plans` - Get all retirement plans
- `POST /api/retirement/plans` - Create new retirement plan
- `GET /api/retirement/plans/{id}/calculate` - Calculate retirement plan

## Configuration

Key configuration options in `.env`:

- `SECRET_KEY`: Secret key for JWT tokens (REQUIRED)
- `DATABASE_URL`: Database connection string
- `EXCHANGE_RATE_API_URL`: Exchange rate API endpoint
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
- `BCRYPT_ROUNDS`: Password hashing rounds (default: 12)
- `ENVIRONMENT`: `development` or `production`
- `DEBUG`: Enable debug mode (false in production)

## Exchange Rate API

The application uses `exchangerate-api.com` by default (free, no API key required). You can configure alternative APIs in the settings.

## Database Models

- **User**: User accounts and authentication
- **Portfolio**: User portfolios
- **Asset**: Assets (stocks, mutual funds, real estate, etc.)
- **Liability**: Liabilities (loans, credit cards, etc.)
- **Insurance**: Insurance policies
- **RetirementPlan**: Retirement planning data

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
Follow PEP 8 style guide. Consider using:
```bash
black app/
flake8 app/
```

## Troubleshooting

### Database Connection Issues
- Ensure database is running
- Check `DATABASE_URL` in `.env`
- Verify database credentials

### Exchange Rate API Issues
- Check internet connectivity
- Verify API endpoint is accessible
- Application will use fallback rates if API fails

### Authentication Issues
- Clear browser cookies
- Verify `SECRET_KEY` is set correctly
- Check token expiration settings

## License

This project is for personal use. Modify and use as needed.

## Support

For issues or questions, please check the code comments or create an issue in your repository.

## Future Enhancements

- [ ] Real-time market data integration
- [ ] Advanced analytics and reporting
- [ ] Export to PDF/Excel
- [ ] Mobile responsive improvements
- [ ] Multi-user support with roles
- [ ] Investment goal tracking
- [ ] Tax planning features
