# Material Web (MD3) Vendored Migration Guide

**Date:** October 19, 2025  
**Status:** Ready to implement  
**Goal:** Migrate from CDN (esm.run) to vendored Material Web components

---

## Current State

**Using:**
```json
{
  "imports": {
    "@material/web/": "https://esm.run/@material/web/"
  }
}
```

**Target:**
```json
{
  "imports": {
    "@lrbf/material-web/": "/static/vendor/material-web/"
  }
}
```

---

## Step 1: Add Material Web Submodule

```bash
# Navigate to your repo root
cd ~/LRBF

# Create packages folder
mkdir -p packages

# Add Material Web as Git submodule
git submodule add https://github.com/material-components/material-web.git packages/material-web

# Initialize and update submodule
git submodule init
git submodule update

# Pin to a specific stable release (recommended)
cd packages/material-web
git checkout v1.5.0  # Use latest stable version
cd ../..

# Commit the submodule
git add .gitmodules packages/material-web
git commit -m "feat: add Material Web as vendored submodule"
```

---

## Step 2: Copy Built Components to Static Folder

Material Web components are pre-built as ES modules. We need to make them accessible via Flask's static folder.

### Option A: Symlink (Recommended - simpler)

```bash
# Create vendor folder in static
mkdir -p static/vendor

# Create symlink from packages to static
cd static/vendor
ln -s ../../packages/material-web material-web
cd ../..

# Verify symlink
ls -la static/vendor/
```

### Option B: Copy Files (Alternative - more explicit)

```bash
# Copy built files to static
mkdir -p static/vendor
cp -r packages/material-web static/vendor/

# Add to .gitignore if using this approach
echo "static/vendor/material-web/" >> .gitignore
```

**Recommendation:** Use **Option A (symlink)** - cleaner and auto-updates when you update the submodule.

---

## Step 3: Update base.html Importmap

**Current (templates/base.html):**
```html
<script type="importmap">
{
  "imports": {
    "@material/web/": "https://esm.run/@material/web/"
  }
}
</script>
```

**New:**
```html
<script type="importmap">
{
  "imports": {
    "@lrbf/material-web/": "{{ url_for('static', filename='vendor/material-web/') }}"
  }
}
</script>
```

**Important:** Update ALL import statements in your templates/JS files:

**Before:**
```javascript
import '@material/web/button/filled-button.js';
```

**After:**
```javascript
import '@lrbf/material-web/button/filled-button.js';
```

---

## Step 4: Test Components

```bash
# Start Flask server
python app.py

# Open browser to http://localhost:5000
```

**Verify:**
- [ ] No 404 errors for MD3 components
- [ ] Buttons, text fields, cards render correctly
- [ ] Dark/light theme toggle works
- [ ] Network tab shows local files (not esm.run CDN)

---

## Troubleshooting

### Components not loading (404)

```bash
# Verify symlink exists
ls -la static/vendor/material-web

# Verify submodule initialized
git submodule update --init
```

### Import errors in browser

Check browser console for:
- "Failed to resolve module specifier" → importmap path wrong
- "404 Not Found" → files not accessible

**Fix:** Ensure importmap uses correct Flask path with `url_for('static', ...)`

---

## Rollback Plan

```bash
# Remove submodule
git submodule deinit -f packages/material-web
git rm -f packages/material-web
rm -rf .git/modules/packages/material-web

# Restore original importmap (CDN version)
git commit -m "chore: rollback MD3 vendoring"
```

---

## Success Criteria

- ✅ No external CDN requests for MD3 components
- ✅ All pages render correctly
- ✅ Components work in light and dark themes
- ✅ Submodule pinned to stable version

---

**Ready to begin? Start with Step 1!**
