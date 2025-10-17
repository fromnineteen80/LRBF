# Railyard Markets - VWAP Recovery Trading Platform

## Material Design 3 Interface

A professional trading platform for executing VWAP Recovery strategies with real-time monitoring and comprehensive analytics.

## Features

- **Morning Report**: Automated stock selection and daily forecasting
- **Live Monitor**: Real-time performance tracking
- **EOD Report**: End-of-day analysis with risk metrics
- **Calculator**: Performance projection tools
- **Practice Mode**: Strategy testing with simulated data
- **History**: Complete trading history and analytics
- **Settings**: Configurable trading parameters
- **API Management**: Credentials for IBKR, Capitalise.ai, and market data

## Quick Start

### Prerequisites

- Python 3.10+
- IBKR account (for live trading)
- Capitalise.ai account (for automated execution)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/fromnineteen80/LRBF.git
cd LRBF
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Access the platform:
```
http://localhost:5000
```

## Default Credentials

- **Username**: admin
- **Password**: admin123

- **Username**: cofounder
- **Password**: luggage2025

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: Material Design 3
- **Database**: SQLite (production: PostgreSQL recommended)
- **Charts**: Chart.js
- **APIs**: IBKR, yfinance, Capitalise.ai

## Project Structure

```
railyard_app/
âââ app.py                 # Main Flask application
âââ modules/               # Backend logic
â   âââ pattern_detector.py
â   âââ stock_selector.py
â   âââ forecast_generator.py
â   âââ ...
âââ templates/             # HTML templates
âââ static/
â   âââ css/              # Material Design 3 styles
â   âââ js/               # JavaScript utilities
âââ data/                 # Database and data files
```

## Configuration

Edit `modules/config.py` to adjust trading parameters:

- Deployment ratio
- Entry/exit thresholds
- Risk limits
- Stock universe

## Deployment

### Railway

1. Connect GitHub repository
2. Set environment variables
3. Deploy automatically

### Local Development

```bash
export FLASK_ENV=development
python app.py
```

## License

Proprietary - The Luggage Room Boys Fund

## Support

For technical issues, contact: [support@railyardmarkets.com]
