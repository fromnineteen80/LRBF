# Quick GitHub Commands

## Initial Setup

```bash
cd railyard_app
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/fromnineteen80/luggageroom.git
git push -u origin main
```

## Daily Workflow

```bash
# Pull latest changes
git pull

# Create feature branch
git checkout -b feature/new-feature

# Make changes, then:
git add .
git commit -m "Description of changes"
git push origin feature/new-feature

# Merge to main (after review)
git checkout main
git merge feature/new-feature
git push origin main
```

## Useful Commands

```bash
# Check status
git status

# View commit history
git log --oneline

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard local changes
git checkout -- .

# Update .gitignore and clean
git rm -r --cached .
git add .
git commit -m "Update .gitignore"
```

## Branching Strategy

- `main`: Production code
- `development`: Integration testing
- `feature/name`: New features
- `bugfix/name`: Bug fixes
- `hotfix/name`: Urgent production fixes
