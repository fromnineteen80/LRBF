# Quick Start Guide

## 🚀 Get Running in 3 Minutes

### Step 1: Extract Archive

```bash
tar -xzf railyard_markets_md3_complete.tar.gz
cd railyard_app
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run Application

```bash
python app.py
```

### Step 4: Access Platform

Open browser: **http://localhost:5000**

Login with:
- **Username**: `admin`
- **Password**: `admin123`

## 🎯 First Steps

1. **Dashboard** - View overview
2. **Morning Report** - Click "Generate Report"
3. **Live Monitor** - Watch real-time updates
4. **Settings** - Adjust configuration

## 📦 What's Included

✅ Complete Material Design 3 interface
✅ All backend modules preserved
✅ 10 functional pages
✅ GitHub ready
✅ Production deployment guides

## 🔧 Configuration

Edit `modules/config.py` to adjust:
- Trading thresholds
- Risk limits
- Stock universe
- Deployment ratios

## 📱 Pages Available

- Login
- Dashboard
- Morning Report
- Live Monitor
- EOD Report
- Calculator
- Practice Mode
- History
- Settings
- API Credentials

## 🐛 Troubleshooting

**Port already in use?**
```bash
# Change port in app.py, line 438
app.run(debug=True, host='0.0.0.0', port=5001)
```

**Module not found?**
```bash
pip install -r requirements.txt
```

**Need help?**
- Check README.md for full documentation
- See DEPLOYMENT_GUIDE.md for production setup
- Review PROJECT_SUMMARY.md for overview

## 🚢 Deploy to Production

See `DEPLOYMENT_GUIDE.md` for:
- Railway deployment (recommended)
- GitHub setup
- Environment variables
- Database migration

## 📚 Documentation Files

- **README.md** - Main documentation
- **PROJECT_SUMMARY.md** - Complete overview
- **DEPLOYMENT_GUIDE.md** - Production deployment
- **GITHUB_COMMANDS.md** - Git workflow
- **QUICKSTART.md** - This file

## 🎨 Material Design 3

Fully compliant with Google's MD3 specifications:
- Design tokens (colors, typography, spacing)
- Component library (buttons, cards, inputs)
- Layout system (navigation rail, top bar)
- Light & dark themes

## ✅ Production Checklist

Before deploying:
- [ ] Update credentials in .env
- [ ] Set FLASK_ENV=production
- [ ] Test all pages
- [ ] Review security settings
- [ ] Configure database
- [ ] Set up monitoring

## 🔐 Security

- Never commit secrets to Git
- Use .env for sensitive data
- Enable HTTPS in production
- Regular security updates

## 📞 Support

Questions? Check the documentation first:
1. README.md
2. PROJECT_SUMMARY.md
3. DEPLOYMENT_GUIDE.md

---

**Ready to trade!** 🚂
