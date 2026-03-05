# TradePulse AI - Intelligent Multi-Asset Trading Analysis Platform

**TradePulse AI** is a comprehensive, production-ready trading analysis application built with FastAPI and Jinja2. It provides intelligent analysis for stocks, cryptocurrencies, commodities, and ETFs with AI-powered insights, portfolio management, and a configurable multi-provider chatbot system.

## ⚠️ Important Disclaimer

**This application is for informational and educational purposes only. This is NOT financial advice.** All trading and investment decisions carry risk. Past performance does not guarantee future results. Always conduct your own research and consult with a qualified financial advisor before making investment decisions. The authors and operators of this application are not responsible for any financial losses.

---

## 🚀 Key Features

### 📊 Multi-Asset Analysis
- **Stocks**: Comprehensive stock analysis (AAPL, TSLA, MSFT, etc.)
- **Cryptocurrencies**: Crypto analysis (BTC, ETH, BNB, etc.)
- **Commodities**: Commodity analysis (Gold, Oil, Silver, etc.)
- **ETFs**: Exchange-traded fund analysis (SPY, QQQ, VTI, etc.)

### 🧠 Core AI Features

#### 1️⃣ AI Buy/Sell Engine
- Combines technical indicators, market structure, trend strength, and volume behavior
- Output: ✅ BUY ❌ SELL ⏸ HOLD with confidence score (0–100%)
- Detailed reasoning for each recommendation

#### 2️⃣ Smart Entry & Exit System
- **Best Buy Zone**: Optimal entry points
- **Partial Profit Targets**: Multiple exit levels
- **Final Exit Price**: Target price for full exit
- Shows "Aggressive Entry" and "Safe Entry" with dynamic updates

#### 3️⃣ AI Stop Loss Manager
- Automatic stop loss based on ATR volatility
- Support & resistance levels
- Risk profile (low/medium/high)
- Trailing stop loss option
- Alerts before stop loss is likely to hit

#### 4️⃣ Technical Analysis Module
- **Unlimited Indicators**: RSI, MACD, EMA, SMA, VWAP, Bollinger Bands, Fibonacci, AI-detected Support & Resistance
- **EMA 20/50/200 Alert System**: Automatic crossover alerts
- Visual charts with plain-English explanations
- Example: "RSI is cooling down from overbought — momentum weakening"

#### 5️⃣ Fundamental Analysis Engine
- For stocks & crypto: Revenue growth, profit margins, debt ratio, cash flow
- Valuation score: Undervalued/Fair/Overvalued
- AI Summary: "Company fundamentals are strong, but current price suggests limited upside short term."

#### 6️⃣ AI Market Scanner
- Scans thousands of assets for breakouts, reversals, volume spikes, trend changes
- Filters: Intraday, Swing, Long-term investing
- Real-time market opportunities

#### 7️⃣ Custom Alerts (No Paid Subscriptions)
- Alerts for Buy/Sell signals, stop loss hit, target reached
- Indicator crossovers
- News + price reaction combo
- Delivery: App notification, email, Telegram/WhatsApp (optional)

#### 8️⃣ Risk Management Dashboard
- Risk per trade calculator
- Position sizing
- Win/Loss expectancy
- Capital protection mode
- AI Tips: "Risk reduced to 1.5% due to high volatility."

#### 9️⃣ Trade Journal + AI Feedback
- Auto-logs trades
- AI reviews your mistakes
- Weekly improvement reports
- Example: "You exit winners too early — consider partial profits."

#### 🔟 Strategy Builder (Advanced)
- Build rules visually: IF/AND/THEN
- Instant backtesting
- AI optimizes parameters

### 💼 Portfolio Management
- Track holdings across all asset types (stocks, crypto, commodities, ETFs)
- Real-time P&L calculation
- Performance metrics (daily, weekly, monthly)
- Asset allocation visualization
- Best/worst performer tracking
- Add/remove holdings with purchase price tracking

### 🤖 AI-Powered Chatbot
- **Multi-Provider Support**: Configure and use multiple AI providers
  - OpenAI (GPT-4, GPT-3.5, GPT-4 Turbo, GPT-4o)
  - Anthropic (Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku)
  - Google (Gemini Pro, Gemini 1.5 Pro, Gemini Flash)
  - Cohere (Command, Command Light)
  - HuggingFace (Llama 2, Mistral, Falcon)
- **User API Key Management**: Enter your own API keys for each provider
- **Model Selection**: Choose from all available models per provider
- **Interactive Chat Interface**: Ask questions about stocks, trading strategies, and analysis
- **Context-Aware**: Maintains conversation history for better responses

### 🔒 Production Security
- **CSRF Protection**: Token-based CSRF protection for all state-changing operations
- **Data Encryption**: Encrypted storage for sensitive data (API keys, portfolios)
- **Input Validation**: Sanitized user inputs to prevent injection attacks
- **Rate Limiting**: Configurable rate limits to prevent abuse (per-user)
- **Security Headers**: XSS protection, content type validation, frame protection
- **Environment Variables**: Secure configuration management
- **JWT Authentication**: Ready for user authentication (optional)

### 📈 Technical Analysis
- **Moving Averages**: SMA 20, 50, 200, EMA 12, 26, 50, 200
- **Momentum Indicators**: RSI, Stochastic Oscillator, Williams %R
- **Trend Indicators**: MACD, ADX
- **Volatility Indicators**: Bollinger Bands, ATR, Keltner Channel
- **Volume Indicators**: VWAP, OBV
- **EMA Alert System**: Automatic alerts for EMA 20/50/200 crossovers
- Real-time technical signals with plain-English explanations

### 📊 Fundamental Analysis
- **Valuation Metrics**: P/E, P/B, PEG, Market Cap
- **Profitability Metrics**: Profit Margin, ROE, ROA, Operating Margin
- **Financial Health**: Debt-to-Equity, Current Ratio, Quick Ratio
- **Growth Metrics**: Revenue Growth, Earnings Growth
- **Dividend Analysis**: Dividend yield and history
- **AI Summaries**: Plain-English explanations of fundamentals

### 🔮 Predictions
- 5-day price predictions using machine learning
- Support and resistance level identification
- Trend analysis
- Confidence scoring

### 📉 Interactive Charts
- Beautiful Plotly charts with technical indicators
- EMA 20/50/200 overlay with alerts
- Interactive time intervals (1m, 5m, 15m, 1h, 1d, 1wk, 1mo)
- Side-by-side comparison charts (1h vs 1d)
- Zoom, pan, and hover for detailed analysis

### ⭐ Watchlist
- Per-user watchlist management
- Quick access to favorite assets
- Auto-analysis on selection
- Right sidebar for easy navigation

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd stock_trading_app
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
```bash
cp .env.example .env
# Edit .env and add your API keys (optional)
```

### Step 4: Set Up AI Provider API Keys (Optional)
You can configure API keys in two ways:

**Option 1: Environment Variables** (for global/default keys)
Add to `.env` file:
```env
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
COHERE_API_KEY=your-cohere-key
HUGGINGFACE_API_KEY=your-huggingface-key
```

**Option 2: User API Keys** (recommended)
- Start the application
- Navigate to Asset Analysis page
- Click "Show" in the "API Key Configuration" section
- Enter your API keys for each provider
- Click "Save" for each provider

---

## 🚀 Usage

### Starting the Application

**Development:**
```bash
python run.py
```

**Production:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8888
```

### Accessing the Application

Open your browser and navigate to:
```
http://localhost:8888
```

### Quick Start Guide

1. **Analyze an Asset**:
   - Go to `/analysis` or click "Asset Analysis" in the sidebar
   - Select asset type (Stock, Crypto, Commodity, or ETF)
   - Enter symbol (e.g., AAPL, BTC, GOLD, SPY)
   - Select time period and interval
   - Click "Analyze"

2. **Manage Portfolio**:
   - Go to `/portfolio` or click "My Portfolio" in the sidebar
   - Click "Add Holding"
   - Enter symbol, asset type, quantity, and purchase price
   - View real-time P&L and performance metrics

3. **Use AI Chatbot**:
   - Configure your API keys (see Installation Step 4)
   - Select an AI provider and model
   - Ask questions about trading, analysis, or strategies

4. **Add to Watchlist**:
   - Use the right sidebar watchlist
   - Enter symbol and click "Add Stock"
   - Click any symbol to auto-analyze

---

## 📁 Project Structure

```
stock_trading_app/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # Application entry point
│   ├── core/                     # Core application components
│   │   ├── __init__.py
│   │   └── config.py            # Configuration management
│   ├── routes/                   # API routes (separated by feature)
│   │   ├── __init__.py
│   │   ├── home.py              # Home page
│   │   ├── analysis.py          # Asset analysis
│   │   ├── portfolio.py         # Portfolio management
│   │   ├── market_scanner.py    # Market scanner
│   │   ├── risk_management.py   # Risk management
│   │   ├── trade_journal.py     # Trade journal
│   │   ├── alerts.py            # Alerts system
│   │   ├── strategy.py          # Strategy builder
│   │   ├── chatbot.py           # AI chatbot
│   │   └── help.py              # Help page
│   ├── services/                 # Business logic services (22 files)
│   │   ├── __init__.py
│   │   ├── data_fetcher.py      # Stock data fetching
│   │   ├── multi_asset_fetcher.py # Multi-asset data fetching
│   │   ├── technical_analyzer.py # Technical analysis
│   │   ├── fundamental_analyzer.py # Fundamental analysis
│   │   ├── enhanced_technical_analyzer.py # Enhanced technical analysis
│   │   ├── enhanced_fundamental_analyzer.py # Enhanced fundamental analysis
│   │   ├── prediction_engine.py # Price predictions
│   │   ├── chart_generator.py   # Chart generation
│   │   ├── recommendation_engine.py # Buy/Sell recommendations
│   │   ├── ai_buy_sell_engine.py # AI buy/sell engine
│   │   ├── smart_entry_exit.py  # Entry/exit system
│   │   ├── ai_stop_loss_manager.py # Stop loss manager
│   │   ├── ai_market_scanner.py # Market scanner
│   │   ├── chatbot_providers.py # Multi-provider chatbot
│   │   ├── risk_management.py  # Risk management
│   │   ├── trade_journal.py     # Trade journal
│   │   ├── alerts_system.py     # Alerts system
│   │   ├── strategy_builder.py  # Strategy builder
│   │   ├── portfolio_manager.py # Portfolio management
│   │   ├── watchlist_manager.py # Watchlist management
│   │   └── user_api_keys.py     # User API key management
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   └── portfolio.py         # Portfolio data models
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── security.py           # Security utilities
│   │   └── rate_limiting.py     # Rate limiting
│   └── middleware/               # Middleware components
│       ├── __init__.py
│       └── security.py           # Security middleware
├── templates/                    # Jinja2 templates
│   ├── base.html                # Base template with navigation
│   ├── home.html                # Home page
│   ├── analysis.html            # Asset analysis page
│   ├── portfolio.html           # Portfolio management page
│   └── help.html               # Help page
├── static/                      # Static files
│   └── logo.svg                # Application logo
├── data/                        # Data storage (JSON files)
│   ├── portfolios.json          # User portfolios
│   ├── watchlists.json          # User watchlists
│   └── user_api_keys.json      # User API keys (encrypted)
├── run.py                       # Application runner
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 🔌 API Endpoints

### Web Interface
- `GET /` or `GET /home` - Home page
- `GET /analysis` - Asset analysis page
- `GET /portfolio` - Portfolio management page
- `GET /market-scanner` - Market scanner
- `GET /risk-management` - Risk management
- `GET /trade-journal` - Trade journal
- `GET /alerts` - Alerts system
- `GET /strategy` - Strategy builder
- `GET /help` - Help page

### Asset Analysis API
- `GET /api/asset/{symbol}/info?asset_type={type}` - Get asset information
- `GET /api/stock/{symbol}/realtime` - Get real-time stock data
- `GET /api/stock/{symbol}/analysis?period=1y` - Get complete analysis as JSON

### Portfolio API
- `GET /api/portfolio` - Get user portfolio
- `POST /api/portfolio/add` - Add holding to portfolio
- `POST /api/portfolio/remove` - Remove holding from portfolio

### Watchlist API
- `GET /api/watchlist` - Get user watchlist
- `POST /api/watchlist/add` - Add stock to watchlist
- `POST /api/watchlist/remove` - Remove stock from watchlist

### Chatbot API
- `GET /api/chatbot/providers` - Get available AI providers and models
- `POST /api/chatbot/chat` - Send chat message to AI provider
- `GET /api/chatbot/models/{provider}` - Get models for a specific provider
- `POST /api/chatbot/keys` - Save API key for a provider
- `GET /api/chatbot/keys` - Get all user API keys (masked)
- `DELETE /api/chatbot/keys/{provider}` - Delete API key for a provider

### Market Scanner API
- `GET /api/market/scan?timeframe={timeframe}&asset_type={type}&signal_type={type}` - Scan market for opportunities
  - `timeframe`: `intraday`, `swing`, `longterm`
  - `asset_type`: `all`, `stock`, `crypto`, `commodity`, `etf`
  - `signal_type`: `all`, `breakout`, `reversal`, `volume`, `trend`

### Health & Status
- `GET /health` - Health check endpoint

---

## 📚 Dependencies

### Core
- **FastAPI**: Modern web framework
- **Jinja2**: Template engine
- **uvicorn**: ASGI server

### Data & Analysis
- **yfinance**: Stock/crypto/commodity data fetching
- **pandas**: Data manipulation
- **numpy**: Numerical computing
- **plotly**: Interactive charts
- **ta**: Technical analysis library
- **scikit-learn**: Machine learning for predictions

### AI Providers
- **openai**: OpenAI GPT models
- **anthropic**: Anthropic Claude models
- **google-generativeai**: Google Gemini models
- **cohere**: Cohere models
- **requests**: HuggingFace API

### Security
- **slowapi**: Rate limiting
- **passlib**: Password hashing
- **python-jose**: JWT tokens
- **python-dotenv**: Environment variables
- **cryptography**: Data encryption

---

## 🔐 Security Features

### Production-Ready Security
1. **CSRF Protection**: Token-based CSRF protection for all POST/PUT/DELETE requests
2. **Data Encryption**: User API keys and sensitive data are encrypted before storage
3. **Input Validation**: All user inputs are sanitized to prevent injection attacks
4. **Rate Limiting**: Per-user rate limiting to prevent abuse and DoS attacks
5. **Security Headers**: Comprehensive security headers on all responses
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY
   - X-XSS-Protection: 1; mode=block
   - Strict-Transport-Security
   - Content-Security-Policy
6. **CORS Protection**: Configurable CORS origins
7. **Environment Variables**: Secure configuration management

---

## 🚀 Production Deployment

### Quick Start
```bash
python run.py
```

### Using Uvicorn Directly
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8888 --reload
```

### Production Checklist
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Set `DEBUG=false` in `.env`
- [ ] Generate secure `SECRET_KEY`
- [ ] Configure `CORS_ORIGINS` with exact domains (not `*`)
- [ ] Enable rate limiting
- [ ] Set up SSL/TLS (use reverse proxy like Nginx)
- [ ] Configure firewall rules
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

### Docker Deployment
```bash
docker build -t tradepulse-ai .
docker run -d -p 8888:8888 --env-file .env tradepulse-ai
```

### Systemd Service (Linux)
Create `/etc/systemd/system/tradepulse-ai.service`:
```ini
[Unit]
Description=TradePulse AI Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/tradepulse-ai
Environment="PATH=/opt/tradepulse-ai/venv/bin"
ExecStart=/opt/tradepulse-ai/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8888
Restart=always

[Install]
WantedBy=multi-user.target
```

### Cloud Platforms
- **Heroku**: `heroku create tradepulse-ai && git push heroku main`
- **Railway**: Connect repository and set environment variables
- **AWS EC2**: Use systemd service configuration
- **Google Cloud Run**: `gcloud run deploy tradepulse-ai --source .`

### Reverse Proxy (Nginx)
Example Nginx configuration:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/TLS Setup
Use Let's Encrypt with Certbot:
```bash
sudo certbot --nginx -d yourdomain.com
```

### Monitoring
- Health Check: `curl http://localhost:8888/health`
- Logs: `docker logs -f tradepulse-ai` or `journalctl -u tradepulse-ai -f`

---

## 💡 Usage Examples

### Analyzing a Stock
1. Navigate to `/analysis`
2. Select "Stock" as asset type
3. Enter symbol (e.g., "AAPL")
4. Select time period (1y) and interval (1d)
5. Click "Analyze"
6. Review comprehensive analysis including:
   - AI Buy/Sell recommendation with confidence score
   - Technical indicators with explanations
   - Fundamental metrics
   - Price predictions
   - Entry/exit levels
   - Stop loss recommendations
   - Interactive charts with EMA alerts

### Analyzing Cryptocurrency
1. Navigate to `/analysis`
2. Select "Crypto" as asset type
3. Enter symbol (e.g., "BTC" or "BTC-USD")
4. Select time period and interval
5. Click "Analyze"
6. Get crypto-specific analysis

### Managing Portfolio
1. Navigate to `/portfolio`
2. Click "Add Holding"
3. Enter:
   - Symbol (e.g., "AAPL")
   - Asset Type (Stock, Crypto, Commodity, or ETF)
   - Quantity (e.g., 10)
   - Purchase Price (e.g., 150.00)
4. View real-time P&L and performance metrics
5. Track best/worst performers
6. Monitor asset allocation

### Using the AI Chatbot
1. Configure API keys (see Installation)
2. Navigate to any analysis page
3. Scroll to "AI Trading Assistant"
4. Select provider and model
5. Ask questions like:
   - "What is the best entry point for AAPL?"
   - "Explain the RSI indicator"
   - "Should I buy TSLA based on current analysis?"
   - "What does the MACD signal mean?"
   - "How do I interpret support and resistance levels?"

### Setting Up Alerts
1. Navigate to `/alerts`
2. Create custom alerts for:
   - Buy/Sell signals
   - Stop loss hits
   - Target reached
   - Indicator crossovers
3. Configure delivery method (app notification, email, etc.)

---

## 🎯 Features by Page

### Home (`/home`)
- Overview of all features
- Quick access to main functions
- Feature highlights

### Asset Analysis (`/analysis`)
- Multi-asset analysis (stocks, crypto, commodities, ETFs)
- AI Buy/Sell recommendations
- Technical analysis with EMA alerts
- Fundamental analysis
- Price predictions
- Entry/exit system
- Stop loss manager
- Interactive charts with multiple time intervals
- Comparison charts (1h vs 1d)

### Portfolio (`/portfolio`)
- Track holdings across all asset types
- Real-time P&L calculation
- Performance metrics
- Asset allocation
- Best/worst performer tracking
- Add/remove holdings

### Market Scanner (`/market-scanner`)
- Scan for breakouts, reversals, volume spikes
- Filter by timeframe (Intraday, Swing, Long-term)
- Real-time opportunities

### Risk Management (`/risk-management`)
- Risk per trade calculator
- Position sizing
- Win/Loss expectancy
- Capital protection mode
- AI risk tips

### Trade Journal (`/trade-journal`)
- Auto-log trades
- AI feedback on trading mistakes
- Weekly improvement reports
- Performance statistics

### Alerts (`/alerts`)
- Custom alert creation
- Buy/Sell signal alerts
- Stop loss alerts
- Target reached alerts
- Indicator crossover alerts

### Strategy Builder (`/strategy`)
- Visual rule building (IF/AND/THEN)
- Instant backtesting
- AI parameter optimization

---

## 📝 Notes

- **Data Source**: Asset data is fetched in real-time using yfinance
- **Predictions**: Use linear regression on historical data
- **Recommendations**: Based on weighted scoring (40% Technical, 35% Fundamental, 25% Predictions)
- **Analysis**: All analysis is performed server-side for accuracy
- **Chatbot**: Requires at least one AI provider API key configured
- **User Data**: Stored in `data/` directory (JSON files) - encrypted for sensitive data
- **Session Management**: Uses cookies for user identification
- **All Features Work Independently**: All tabs and features work without requiring stock input first. You can navigate to any feature page directly and use it independently.

---

## 🔄 Import Paths

### New Structure (Current)
```python
from app.core.config import settings
from app.services.multi_asset_fetcher import MultiAssetFetcher
from app.services.technical_analyzer import TechnicalAnalyzer
from app.services.ai_buy_sell_engine import AIBuySellEngine
from app.services.portfolio_manager import PortfolioManager
```

### Legacy Structure (Deprecated)
```python
from config import settings
from data_fetcher import StockDataFetcher
from technical_analyzer import TechnicalAnalyzer
```

---

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- Security best practices are maintained
- Tests are added for new features
- Documentation is updated

---

## 📄 License

This project is for educational and research purposes.

---

## 🆘 Support

For help and documentation:
- Visit `/help` page in the application
- Check the FAQ section
- Review the user guide

---

## 📋 Routes Status & Functionality

### Main Pages
1. **`/` or `/home`** - Home page with feature overview
2. **`/analysis`** - Asset Analysis page (stocks, crypto, commodities, ETFs)
3. **`/portfolio`** - Portfolio Management
4. **`/market-scanner`** - Market Scanner
5. **`/risk-management`** - Risk Management
6. **`/trade-journal`** - Trade Journal
7. **`/alerts`** - Custom Alerts
8. **`/strategy`** - Strategy Builder
9. **`/help`** - Help & Documentation

### API Endpoints
- `/api/portfolio` - Portfolio operations
- `/api/watchlist` - Watchlist operations
- `/api/chatbot/*` - AI chatbot endpoints
- `/health` - Health check

## 🎨 Theme Toggle

- Dark/Light mode toggle button in header
- Theme preference saved in localStorage
- Smooth switching between themes
- All components styled for both themes

---

## 📊 Version

**Current Version**: 2.0.0

**What's New in v2.0.0**:
- ✅ Multi-asset support (stocks, crypto, commodities, ETFs)
- ✅ Portfolio management with real-time P&L
- ✅ Enhanced security (CSRF, encryption, input validation)
- ✅ User API key management
- ✅ EMA 20/50/200 alert system
- ✅ Interactive time intervals
- ✅ Comparison charts (1h vs 1d)
- ✅ Production-ready project structure
- ✅ Financial disclaimer on all pages
- ✅ Fixed sidebar navigation
- ✅ Dark/Light theme toggle
- ✅ All routes functional

---

**Built with ❤️ for intelligent trading analysis**
