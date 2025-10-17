# Railyard Markets - VWAP Recovery Trading Platform

> **⚠️ IMPORTANT FOR CLAUDE ASSISTANTS:**
> - DO NOT review past conversation history unless explicitly given a session number by the user
> - DO NOT update this README or create summary documents unless explicitly requested
> - Past conversations may contain errors - work only from current session instructions



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
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ app.py                 # Main Flask application
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ modules/               # Backend logic
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ pattern_detector.py
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ stock_selector.py
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ forecast_generator.py
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ ...
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ templates/             # HTML templates
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ static/
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ css/              # Material Design 3 styles
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ js/               # JavaScript utilities
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ data/                 # Database and data files
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
