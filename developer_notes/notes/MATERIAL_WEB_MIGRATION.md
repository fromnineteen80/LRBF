# 🚂 Railyard Markets - Material Web Components Migration Guide

## 🎯 Project Overview

The Luggage Room Boys Fund - VWAP Recovery Trading Platform
- **Status**: Migrating to Official Material Design 3
- **Current**: Custom MD3 CSS implementation
- **Target**: Google's official Material Web Components
- **Repository**: https://github.com/fromnineteen80/luggageroom

---

## 📦 What We're Doing

### Phase 1: GitHub Setup (5 minutes)
### Phase 2: Material Web Installation (10 minutes)
### Phase 3: Template Migration (Per page, ~30 min each)
### Phase 4: Theme Integration (Your custom colors)
### Phase 5: Testing & Deployment

---

## Phase 1: GitHub Setup

### Step 1: Initialize Git

```bash
cd railyard_app

# Initialize repository
git init

# Add all files
git add .

# First commit
git commit -m "Initial commit: Railyard Markets with custom MD3"
```

### Step 2: Connect to GitHub

```bash
# Add remote repository
git remote add origin https://github.com/fromnineteen80/luggageroom.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Verify

Go to: https://github.com/fromnineteen80/luggageroom
You should see all your files!

---

## Phase 2: Install Material Web Components

### Option A: npm (Recommended for Development)

```bash
# Install Node.js if needed (check with: node --version)
# Then install Material Web:
npm install

# This installs @material/web from package.json
# Components will be in: node_modules/@material/web/
```

### Option B: CDN (Quick Start)

Add to your HTML templates (we'll do this):

```html
<script type="importmap">
{
  "imports": {
    "@material/web/": "https://esm.run/@material/web/"
  }
}
</script>
```

### What You Get

Official Material Web Components:
- `<md-filled-button>` - Buttons
- `<md-outlined-card>` - Cards
- `<md-text-field>` - Input fields
- `<md-navigation-rail>` - Side navigation
- `<md-top-app-bar>` - Top bar
- `<md-icon>` - Material icons
- `<md-list>` - Lists
- `<md-menu>` - Menus
- `<md-dialog>` - Dialogs
- And 30+ more components!

Full component list: https://github.com/material-components/material-web

---

## Phase 3: Template Migration Strategy

### Current Structure
```
templates/
├── base.html          # Master template
├── login.html         # Authentication
├── dashboard.html     # Main dashboard
├── morning.html       # Morning report
├── live.html          # Live monitoring
├── eod.html           # EOD analysis
├── calculator.html    # Performance calculator
├── practice.html      # Practice mode
├── history.html       # Trading history
├── settings.html      # Configuration
└── api_credentials.html # API management
```

### Migration Approach

We'll migrate **one component at a time**, starting with:

1. **base.html** - Master template (navigation rail, app bar)
2. **login.html** - Simple page, good starting point
3. **dashboard.html** - Test cards and buttons
4. **morning.html** - Forms and data display
5. Then the rest...

---

## Phase 4: Your Custom Theme Integration

### Your Color Theme (From uploaded CSS)

You have custom MD3 color tokens in:
- `light.css` - Light theme colors
- `dark.css` - Dark theme colors
- `light-hc.css` - High contrast light
- `dark-hc.css` - High contrast dark
- `light-mc.css` - Medium contrast light
- `dark-mc.css` - Medium contrast dark

### Applying Custom Colors to Material Web

Material Web uses CSS custom properties (same as your theme!):

```css
/* Your theme colors */
--md-sys-color-primary: rgb(38 106 73);
--md-sys-color-on-primary: rgb(255 255 255);
/* ...etc */
```

Material Web components automatically read these! We just need to:

1. Load your theme CSS files
2. Apply the `.light` or `.dark` class to `<html>` element
3. Material Web components will use your colors automatically

**This is great news** - your custom theme is already compatible!

---

## Phase 5: Implementation Plan

### Week 1: Setup & Base Template

**Day 1-2: GitHub & Material Web Setup**
- ✅ Initialize Git
- ✅ Push to GitHub
- ✅ Install Material Web Components
- ✅ Set up CDN imports

**Day 3-4: Migrate base.html**
- Convert navigation rail to `<md-navigation-rail>`
- Convert app bar to `<md-top-app-bar>`
- Apply your custom theme
- Test theme toggle

**Day 5: Migrate login.html**
- Convert form to Material Web components
- Test authentication flow

### Week 2: Core Pages

**Day 1-2: dashboard.html**
- Cards → `<md-outlined-card>`
- Buttons → `<md-filled-button>`, `<md-outlined-button>`
- Charts (keep Chart.js)

**Day 3-4: morning.html & live.html**
- Data tables → `<md-list>` or custom styled
- Action buttons → Material buttons
- Form inputs → `<md-text-field>`

**Day 5: eod.html**
- Similar to morning/live
- Chart integration

### Week 3: Supporting Pages & Polish

**Day 1-2: calculator.html, practice.html, history.html**
- Forms and inputs
- Results display

**Day 3-4: settings.html, api_credentials.html**
- Configuration UI
- Status indicators

**Day 5: Testing & Refinement**
- Cross-browser testing
- Responsive design check
- Theme toggle testing

---

## 🎨 Component Mapping Guide

### Current → Material Web

| Current HTML | Material Web Component | Notes |
|-------------|------------------------|-------|
| `<button class="primary">` | `<md-filled-button>` | Filled style |
| `<button class="secondary">` | `<md-outlined-button>` | Outlined style |
| `<button class="text">` | `<md-text-button>` | Text style |
| `<input type="text">` | `<md-text-field>` | Text input |
| `<input type="password">` | `<md-text-field type="password">` | Password input |
| `<div class="card">` | `<md-outlined-card>` | Card container |
| `<nav class="rail">` | `<md-navigation-rail>` | Side navigation |
| `<header class="app-bar">` | Custom div with MD3 styles | App bar (component coming) |
| `<select>` | `<md-select>` | Dropdown |
| `<dialog>` | `<md-dialog>` | Modal dialog |

---

## 📁 New File Structure

After migration:

```
railyard_app/
├── static/
│   ├── css/
│   │   ├── theme/              # Your custom theme
│   │   │   ├── light.css       # ✅ Already have
│   │   │   ├── dark.css        # ✅ Already have
│   │   │   ├── light-hc.css    # ✅ Already have
│   │   │   ├── dark-hc.css     # ✅ Already have
│   │   │   ├── light-mc.css    # ✅ Already have
│   │   │   └── dark-mc.css     # ✅ Already have
│   │   └── custom.css          # Any additional custom styles
│   ├── js/
│   │   ├── theme-toggle.js     # Light/dark mode switcher
│   │   ├── common.js           # Utilities
│   │   └── charts.js           # Chart.js integration
│   └── node_modules/           # Material Web (if using npm)
│       └── @material/
│           └── web/
├── templates/
│   ├── base.html               # Updated with Material Web
│   └── ...all other templates...
├── modules/                     # Backend (unchanged!)
├── package.json                # npm configuration
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

---

## 🚀 Quick Start: First Steps

### 1. Push Current Code to GitHub

```bash
cd railyard_app
git init
git add .
git commit -m "Initial commit: Pre-migration state"
git remote add origin https://github.com/fromnineteen80/luggageroom.git
git push -u origin main
```

### 2. Create Development Branch

```bash
git checkout -b material-web-migration
```

Work on this branch, then merge to main when ready.

### 3. Install Material Web

```bash
npm install
```

### 4. Test Current App

```bash
python app.py
```

Visit: http://localhost:5000

---

## 📚 Documentation & Resources

### Official Material Web
- **Repository**: https://github.com/material-components/material-web
- **Components**: https://material-web.dev/
- **Theming Guide**: https://material-web.dev/theming/
- **Migration Guide**: https://material-web.dev/about/roadmap/

### Material Design 3
- **Guidelines**: https://m3.material.io/
- **Color System**: https://m3.material.io/styles/color
- **Typography**: https://m3.material.io/styles/typography
- **Theming**: https://m3.material.io/foundations/customization

### Your Project Docs
- `START_HERE.md` - Original setup guide
- `PROJECT_SUMMARY.md` - Feature overview
- `Railyard_Specs.md` - Complete specifications
- `DEPLOYMENT_GUIDE.md` - Production deployment

---

## ✅ Migration Checklist

### Setup
- [ ] GitHub repository initialized
- [ ] Pushed to GitHub
- [ ] Material Web installed (npm or CDN configured)
- [ ] Custom theme files moved to static/css/theme/

### Templates (Base)
- [ ] base.html - Master template with Material Web components
- [ ] Theme toggle implemented
- [ ] Navigation rail converted
- [ ] App bar converted

### Templates (Pages)
- [ ] login.html
- [ ] dashboard.html
- [ ] morning.html
- [ ] live.html
- [ ] eod.html
- [ ] calculator.html
- [ ] practice.html
- [ ] history.html
- [ ] settings.html
- [ ] api_credentials.html

### Testing
- [ ] All pages load correctly
- [ ] Theme toggle works
- [ ] Forms submit properly
- [ ] API endpoints functional
- [ ] Charts display correctly
- [ ] Responsive on mobile
- [ ] Cross-browser tested

### Deployment
- [ ] Production environment variables set
- [ ] IBKR credentials configured
- [ ] Capitalise.ai credentials configured
- [ ] Database migrations complete
- [ ] Railway deployment successful

---

## 🔧 Development Workflow

### Daily Workflow

```bash
# Start your day
git pull origin material-web-migration
python app.py  # Test locally

# Make changes to templates
# ...edit files...

# Test
# Visit http://localhost:5000

# Commit
git add .
git commit -m "feat: migrate dashboard.html to Material Web"
git push origin material-web-migration
```

### Commit Message Convention

```
feat: Add new feature
fix: Bug fix
style: UI/styling changes
refactor: Code refactoring
docs: Documentation updates
test: Testing updates
```

---

## 🐛 Common Issues & Solutions

### Issue: Material Web components not rendering

**Solution**: Check that importmap is in `<head>`:

```html
<script type="importmap">
{
  "imports": {
    "@material/web/": "https://esm.run/@material/web/"
  }
}
</script>
```

### Issue: Custom colors not applying

**Solution**: Ensure theme CSS loaded BEFORE Material Web:

```html
<link rel="stylesheet" href="/static/css/theme/light.css">
<script type="module" src="https://esm.run/@material/web/..."></script>
```

### Issue: Theme toggle not working

**Solution**: Toggle class on `<html>` element:

```javascript
document.documentElement.classList.toggle('dark');
document.documentElement.classList.toggle('light');
```

---

## 📞 Next Steps

1. **Read this document completely** ✅ You're here!
2. **Push to GitHub** (see "Quick Start" above)
3. **Install Material Web** (npm install)
4. **Start with base.html** (master template)
5. **Migrate one page at a time**
6. **Test frequently**
7. **Deploy when ready**

---

## 💡 Tips for Success

- **Commit often** - Small, frequent commits are easier to manage
- **Test in browser** - Check each change in real browser
- **One component at a time** - Don't try to migrate everything at once
- **Keep backend unchanged** - All modules/* files stay the same
- **Use branches** - Work on `material-web-migration` branch
- **Read Material Web docs** - Bookmark https://material-web.dev/

---

## 🎉 You're Ready!

This guide has everything you need to:
1. Set up GitHub properly
2. Install official Material Web Components
3. Migrate your custom MD3 → Material Web
4. Apply your custom theme
5. Deploy to production

**Your backend is safe** - we're only changing HTML/CSS!

---

**Version**: 1.0.0 - Migration Guide
**Date**: October 14, 2025
**Status**: Ready to Start 🚀
