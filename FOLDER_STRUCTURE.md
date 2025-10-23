# LRBF Folder Structure

## Overview
This document describes the folder organization for the LRBF trading platform, following industry-standard patterns used by professional trading firms like Robinhood, Interactive Brokers, and TD Ameritrade.

## Root Directory
```
LRBF/
├── app.py                  # Flask application entry point
├── requirements.txt        # Python dependencies
├── start.sh               # Production startup script
├── Makefile               # Development commands
├── package.json           # Node.js dependencies (Material Design 3)
├── .gitignore             # Git ignore rules
└── FILE_TREE.txt          # Complete file tree
```

## Backend Structure
All Python business logic, organized by function:

```
backend/
├── __init__.py
├── api/                   # Flask API endpoints (future)
│   ├── __init__.py
│   ├── auth.py           # Authentication endpoints
│   ├── morning.py        # Morning report endpoints
│   ├── live.py           # Live monitoring endpoints
│   ├── eod.py            # End-of-day endpoints
│   └── admin.py          # Admin endpoints
├── core/                  # Core trading algorithms
│   ├── __init__.py
│   ├── pattern_detector.py    # VWAP recovery pattern detection
│   ├── stock_selector.py      # Portfolio stock selection (2/4/2 balance)
│   ├── forecast_generator.py  # Daily performance forecasting
│   ├── metrics_calculator.py  # Risk-adjusted metrics (Sharpe, Sortino)
│   └── batch_analyzer.py      # Batch stock analysis
├── data/                  # Data providers and market interfaces
│   ├── __init__.py
│   ├── ibkr_connector.py      # Interactive Brokers API client
│   ├── data_provider.py       # yfinance wrapper
│   ├── market_calendar.py     # Trading calendar (NYSE/NASDAQ)
│   └── stock_universe.py      # Curated stock list
├── models/                # Database models and ORM
│   ├── __init__.py
│   └── database.py            # SQLite database operations
├── services/              # External service integrations
│   ├── __init__.py
│   ├── email_service.py       # SendGrid email service
│   ├── sms_service.py         # Twilio SMS service
│   └── capitalise_prompts.py  # Capitalise.ai prompt generator
├── reports/               # Report generation
│   ├── __init__.py
│   ├── morning_report.py      # Morning analysis & stock selection
│   ├── live_monitor.py        # Real-time monitoring
│   ├── eod_reporter.py        # End-of-day analysis
│   └── eod_html_generator.py  # EOD HTML report generator
└── utils/                 # Utility functions
    ├── __init__.py
    ├── auth_helper.py         # Authentication helpers
    ├── simulation_helper.py   # Simulation mode helpers
    └── scheduler.py           # Task scheduler
```

## Frontend Structure
All user-facing code (HTML, CSS, JavaScript):

```
frontend/
├── templates/             # Jinja2 HTML templates
│   ├── base.html         # Base template (Material Design 3)
│   ├── dashboard.html    # Main overview
│   ├── morning.html      # Morning report page
│   ├── live.html         # Live monitoring page
│   ├── eod.html          # End-of-day analysis page
│   ├── calculator.html   # Performance calculator
│   ├── practice.html     # Strategy testing (simulation)
│   ├── history.html      # Trading history
│   ├── settings.html     # Configuration (admin)
│   ├── api_credentials.html  # API key management (admin)
│   ├── fund.html         # Fund information
│   ├── ledger.html       # Financial transparency (admin)
│   ├── documents.html    # File storage (admin)
│   ├── profile.html      # User settings
│   ├── performance.html  # Metrics dashboard
│   ├── about.html        # About the fund
│   ├── how_it_works.html # Strategy explanation
│   ├── glossary.html     # Educational content
│   ├── login.html        # Authentication
│   ├── signup.html       # New user registration
│   ├── 404.html          # Not found error
│   └── 500.html          # Server error
└── static/               # Static assets
    ├── css/
    │   ├── material-web-layout.css  # Material Design 3 layout
    │   ├── md3-theme.css            # MD3 theme variables
    │   └── theme/                   # Theme variations
    │       ├── light.css
    │       ├── dark.css
    │       ├── light-hc.css         # High contrast
    │       ├── dark-hc.css
    │       ├── light-mc.css         # Medium contrast
    │       └── dark-mc.css
    └── js/
        ├── common.js              # Shared utilities
        ├── documents.js           # Document management
        ├── fund.js                # Fund page logic
        ├── ledger.js              # Ledger page logic
        ├── market-status.js       # Market status indicator
        ├── profile.js             # Profile page logic
        └── theme-controller.js    # Theme switching
```

## Configuration & Scripts
```
config/
├── __init__.py
└── config.py              # Application configuration

scripts/
├── migrate_db.py          # Database migration script
└── migrate_wall_street.py # Wall Street data migration
```

## Tests
```
tests/
├── __init__.py
├── unit/                  # Unit tests (future)
├── integration/           # Integration tests
│   ├── __init__.py
│   └── test_morning_report.py
└── benchmarks/            # Performance benchmarks (future)
```

## Data & Logs
```
data/
├── luggage_room.db        # SQLite database (dev)
└── backups/               # Database backups

logs/
└── *.log                  # Application logs
```

## Documentation
```
docs/
└── (strategy documents, technical specs)

developer_notes/
└── (development notes, ADRs)

prototypes/
└── (experimental code)
```

## Why This Structure?

### Industry Standard
This structure follows patterns used by professional trading platforms:
- **Robinhood**: Separates frontend (React) from backend (Python/Django)
- **Interactive Brokers**: Organizes by business function (data, trading, reporting)
- **TD Ameritrade**: Clear separation of concerns (core logic, APIs, UI)

### Benefits
1. **Scalability**: Easy to add new features without restructuring
2. **Team Collaboration**: Clear ownership (frontend team, backend team, infra team)
3. **Testing**: Each module can be tested independently
4. **Deployment**: Frontend and backend can be deployed separately
5. **Maintenance**: Clear file locations reduce search time
6. **Onboarding**: New developers understand structure immediately

### Key Principles
- **Backend**: All Python logic organized by function (core, data, models, services)
- **Frontend**: All user-facing code in one place
- **Config**: Environment-specific settings isolated
- **Scripts**: One-time operations separated from application code
- **Tests**: Organized by type (unit, integration, benchmarks)

## Migration Notes
Previous structure used flat `modules/` directory. This caused:
- Hard to find specific functionality
- No clear separation between trading logic and UI
- Difficult to scale (all modules in one folder)

New structure provides:
- Clear separation (backend vs frontend)
- Logical grouping (core vs data vs services)
- Room to grow (easy to add new subdirectories)
