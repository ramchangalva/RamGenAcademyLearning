# Branch Management Guide

## Branch Structure

This repository uses a two-branch workflow:

### 🌿 **master** Branch
- **Purpose**: Production-ready, stable code
- **Use for**: Releases, stable features, main deployment
- **Protection**: Should be kept stable and tested

### 🔧 **work** Branch  
- **Purpose**: Development and experimental features
- **Use for**: New features, bug fixes, testing, experimentation
- **Protection**: Can be more experimental, allows for breaking changes

## Branch Workflow

### Starting New Work
```bash
# Switch to work branch
git checkout work

# Create a feature branch from work (optional)
git checkout -b feature/new-feature-name

# Make your changes and commit
git add .
git commit -m "Add new feature"

# Push to work branch
git push origin work
```

### Merging Work to Master
```bash
# Ensure work branch is up to date
git checkout work
git pull origin work

# Switch to master
git checkout master

# Merge work into master
git merge work

# Push to master
git push origin master
```

### Syncing Branches
```bash
# Update work branch with latest master changes
git checkout work
git merge master

# Or update master with work changes
git checkout master
git merge work
```

## Best Practices

1. **Always test on `work` branch first** before merging to `master`
2. **Keep `master` stable** - only merge tested, working code
3. **Use feature branches** for larger features (branch from `work`)
4. **Regular sync** - keep both branches relatively in sync
5. **Clear commit messages** - describe what and why

## Current Branch Status

- ✅ **master**: Production-ready code
- ✅ **work**: Development branch (synced with master)

## Pushing Both Branches to GitHub

After creating the repository on GitHub:

```bash
# Push master branch
git checkout master
git push -u origin master

# Push work branch
git checkout work
git push -u origin work
```

Or push both at once:
```bash
git push origin --all
```
