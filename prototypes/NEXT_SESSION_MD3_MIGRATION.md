# NEXT SESSION: MD3 Vendored Migration

**Date Created:** October 19, 2025  
**Status:** Ready to Execute  
**Estimated Time:** 30-60 minutes  

---

## 🎯 WHAT WE'RE DOING

Migrating from CDN-hosted Material Web components to local vendored components.

**Current State:**
- ❌ Using `https://esm.run/@material/web/` (external CDN)
- ❌ External dependency, no version control

**Target State:**
- ✅ Local components at `/packages/material-web`
- ✅ Full version control via Git submodule
- ✅ Alias: `@lrbf/material-web/`

---

## 📁 FILES CREATED THIS SESSION

1. ✅ **docs/canonical_repo_layout.md** - Project structure reference
2. ✅ **docs/project_layout_beta.md** - Beta environment layout
3. ✅ **docs/policy_matrix.yaml** - Executable policy rules
4. ✅ **docs/rules_to_follow.md** - Complete engineering standards (sections 0-13.3)
5. ✅ **docs/lrbf_data_reference.md** - Summary placeholder (full 487-point table in attachment)
6. ✅ **docs/MD3_VENDORED_MIGRATION.md** - Complete migration guide

**Note:** The full lrbf_data_reference.md with all 487 data points is in the attached document. Upload manually if needed.

---

## 🚀 NEXT SESSION PROMPT

Copy/paste this into your next conversation:

```
I'm ready to execute the MD3 Vendored Migration for my LRBF project.

CONTEXT:
- Migration guide: docs/MD3_VENDORED_MIGRATION.md
- Policy docs: docs/rules_to_follow.md, docs/policy_matrix.yaml
- Current state: Using CDN (@material/web from esm.run)
- Target: Vendored local components (@lrbf/material-web)

ANALYSIS FROM LAST SESSION:
- Only 1 file needs updates: templates/base.html
- 33 import statements need prefix change
- 1 importmap needs update
- All /static/js/ and /static/css/ files are SAFE (no changes needed)

TASK:
1. Help me execute Step 1 (Git submodule setup) with exact commands
2. Update templates/base.html (Steps 2-3):
   - Change importmap from @material/web/ to @lrbf/material-web/
   - Change all 33 import statements
3. Commit and push changes
4. Guide me through testing/verification

Please proceed step-by-step and confirm each step before moving forward.
```

---

## 📊 WHAT WE CONFIRMED THIS SESSION

### ✅ Safe Files (No Changes Needed):
- **7 JavaScript files:** common.js, documents.js, fund.js, ledger.js, market-status.js, profile.js, theme-controller.js
- **~10 CSS files:** All theme files and custom CSS
- **All HTML templates except base.html**

### ⚠️ Files That Need Updates:
- **templates/base.html** (1 file):
  - Line 1: Importmap (1 change)
  - Lines 2-34: Import statements (33 changes)

### 📦 Changes Required:
| Item | Current | Target |
|------|---------|--------|
| Importmap alias | @material/web/ | @lrbf/material-web/ |
| Importmap URL | https://esm.run/@material/web/ | {{ url_for('static', filename='vendor/material-web/') }} |
| All import paths | @material/web/ | @lrbf/material-web/ |

---

## 🛠️ STEP-BY-STEP CHECKLIST

### Step 1: Git Submodule Setup (Do Locally)
```bash
cd ~/LRBF
mkdir -p packages
git submodule add https://github.com/material-components/material-web.git packages/material-web
git submodule init && git submodule update
cd packages/material-web && git checkout v1.5.0 && cd ../..
mkdir -p static/vendor
cd static/vendor && ln -s ../../packages/material-web material-web && cd ../..
ls -la static/vendor/material-web  # Verify
```

### Step 2: Update base.html (Claude Can Help)
- [ ] Update importmap (1 change)
- [ ] Update all import statements (33 changes)
- [ ] Verify no typos

### Step 3: Commit & Push
```bash
git add .gitmodules packages/material-web static/vendor templates/base.html
git commit -m "feat: migrate to vendored Material Web components"
git push
```

### Step 4: Test
```bash
python app.py
# Open http://localhost:5000
# Check browser console (no 404s)
# Check Network tab (shows /static/vendor/material-web/)
```

---

## 🔄 ROLLBACK PLAN (If Something Breaks)

```bash
git submodule deinit -f packages/material-web
git rm -f packages/material-web
rm -rf .git/modules/packages/material-web
rm -rf static/vendor/material-web
git checkout HEAD templates/base.html
git commit -m "chore: rollback MD3 vendoring"
git push
```

---

## ✅ SUCCESS CRITERIA

- [ ] No external CDN requests for MD3 components
- [ ] All pages render identically to before
- [ ] /packages/material-web folder exists
- [ ] /static/vendor/material-web symlink works
- [ ] base.html uses @lrbf/material-web/ alias
- [ ] Browser console clean (no errors)
- [ ] All 23 HTML pages still work

---

## 📚 REFERENCE DOCS (In Your Repo)

- **Migration Guide:** docs/MD3_VENDORED_MIGRATION.md
- **Rules:** docs/rules_to_follow.md (sections 0-13.3)
- **Policy Matrix:** docs/policy_matrix.yaml
- **Project Layout:** docs/project_layout_beta.md
- **Data Reference:** docs/lrbf_data_reference.md

---

## 💡 TIPS FOR NEXT SESSION

1. **Start with the prompt above** - It has all the context
2. **Do Step 1 first** - Git commands in your terminal
3. **Let Claude handle Step 2** - It can update base.html via GitHub API
4. **Test immediately after** - Catch any issues early
5. **Keep rollback plan handy** - Just in case

---

## 🎯 EXPECTED OUTCOME

After successful migration:
- Material Web loads from `/static/vendor/material-web/` (local)
- Zero visual changes to UI
- Faster page loads (no external HTTP requests)
- Compliant with policy_matrix.yaml rules
- Full version control over MD3 components

---

**Ready for next session!** 🚀

All documentation is in place. The migration is straightforward and low-risk.
