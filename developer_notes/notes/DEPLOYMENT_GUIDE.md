# Deployment Guide - Railyard Markets

## GitHub Setup

### 1. Initialize Repository

```bash
cd railyard_app
git init
git add .
git commit -m "Initial commit: Material Design 3 implementation"
```

### 2. Connect to GitHub

```bash
git remote add origin https://github.com/fromnineteen80/luggageroom.git
git branch -M main
git push -u origin main
```

### 3. Branch Strategy

- `main`: Production-ready code
- `development`: Integration branch
- `feature/*`: Feature branches

## Local Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

### Access

- URL: http://localhost:5000
- Login: admin / admin123

## Production Deployment (Railway)

### 1. Prepare for Deployment

Create `Procfile`:
```
web: gunicorn app:app
```

Update `requirements.txt`:
```bash
pip freeze > requirements.txt
```

### 2. Deploy to Railway

1. Go to railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `luggageroom` repository
5. Railway auto-detects Python and deploys

### 3. Environment Variables

Set in Railway dashboard:

```
FLASK_ENV=production
SECRET_KEY=<generate-random-key>
IBKR_API_KEY=<your-key>
IBKR_API_SECRET=<your-secret>
CAPITALISE_API_KEY=<your-key>
DATABASE_URL=<railway-postgres-url>
```

### 4. Database Migration

For production, migrate from SQLite to PostgreSQL:

```bash
# Install psycopg2
pip install psycopg2-binary

# Update database.py to support PostgreSQL
# Railway provides DATABASE_URL automatically
```

## API Configuration

### Interactive Brokers (IBKR)

1. Create IBKR account
2. Enable API access
3. Get API credentials
4. Add to environment variables

### Capitalise.ai

1. Sign up at capitalise.ai
2. Get API key
3. Add to environment variables

### yfinance

- Free, no API key needed
- Set `USE_SIMULATION=False` in production

## Monitoring

### Logs

Railway provides real-time logs:
```bash
railway logs
```

### Health Check

Monitor `/api/system/status` endpoint for system health.

## Backup

### Database Backup

```bash
# SQLite backup
cp data/luggage_room.db data/backups/luggage_room_$(date +%Y%m%d).db

# PostgreSQL backup (Railway)
railway run pg_dump > backup.sql
```

### Code Backup

Regular git commits and pushes to GitHub.

## Troubleshooting

### Common Issues

1. **Module not found**
   - Solution: `pip install -r requirements.txt`

2. **Port already in use**
   - Solution: Change port in app.py or kill existing process

3. **Database locked**
   - Solution: Close other connections to database

4. **IBKR connection failed**
   - Solution: Check API credentials and network

## Security

### Best Practices

1. Never commit secrets to Git
2. Use environment variables for sensitive data
3. Enable HTTPS in production (Railway provides this)
4. Regular security updates: `pip install --upgrade -r requirements.txt`
5. Strong passwords for user accounts

## Performance Optimization

### Production Tips

1. Enable Flask caching
2. Use CDN for static assets
3. Optimize database queries
4. Enable gzip compression
5. Monitor response times

## Maintenance

### Regular Tasks

1. Daily: Check logs for errors
2. Weekly: Review trading performance
3. Monthly: Update dependencies
4. Quarterly: Database cleanup

## Support

For deployment issues:
- Check Railway status: status.railway.app
- Review logs
- Contact support@railyardmarkets.com
