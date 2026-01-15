# Development Setup Guide

This guide explains how to work with the development branch while keeping production running.

## Quick Start

### 1. Create Development Database

First, create a separate database for development:

```bash
# Using PostgreSQL (example)
createdb mindos_development

# Or using psql
psql -U your_user -c "CREATE DATABASE mindos_development;"
```

### 2. Set Up Development Environment

```bash
# Copy the example environment file
cp .env.development.example .env.development

# Edit .env.development and update DATABASE_URL to point to your development database
# Make sure to use a different database name than production!
```

### 3. Create Development Branch

```bash
# Make sure you're on main and it's up to date
git checkout main
git pull origin main

# Create and switch to development branch
git checkout -b development

# Push to remote (optional)
git push -u origin development
```

## Running the App

### Production (Terminal 1)

```bash
./scripts/run_production.sh
```

This will:
- Switch to `main` branch
- Set `ENVIRONMENT=production`
- Load `.env` file
- Run on `http://localhost:8501`
- Disable hot-reload for stability

### Development (Terminal 2)

```bash
./scripts/run_development.sh
```

This will:
- Switch to `development` branch
- Set `ENVIRONMENT=development`
- Load `.env.development` (or `.env` as fallback)
- Run on `http://localhost:8502`
- Enable hot-reload for development

## Development Workflow

### Daily Development

1. **Start Production** (if not already running)
   ```bash
   ./scripts/run_production.sh
   ```

2. **Start Development**
   ```bash
   ./scripts/run_development.sh
   ```

3. **Make Changes**
   - Edit code in your IDE
   - Test in development instance (`http://localhost:8502`)
   - Production remains stable (`http://localhost:8501`)

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: description of changes"
   git push origin development
   ```

### Merging to Production

When your changes are tested and ready:

```bash
# Switch to main
git checkout main
git pull origin main

# Merge development branch
git merge development

# Push to production
git push origin main

# Restart production app (Ctrl+C and run ./scripts/run_production.sh again)
```

## Database Migrations

### Creating a Migration

1. Create a new file in `migrations/`:
   ```bash
   migrations/migration_XXX_your_description.py
   ```

2. Follow the template in `migrations/README.md`

3. Test in development first:
   ```python
   from migrations.migration_XXX_your_description import up
   up()
   ```

4. When ready, apply to production (after merging to main)

### Important Notes

- ⚠️ **Never run development migrations on production database**
- ✅ Always test migrations in development first
- ✅ Make migrations reversible (include `down()` function)
- ✅ Use `IF NOT EXISTS` / `IF EXISTS` for safety

## Environment Variables

### Production (`.env`)
- Uses production database
- Production API keys
- Stable configuration

### Development (`.env.development`)
- Uses development database
- Can use test API keys
- Development-specific settings

Both files are gitignored to protect your secrets.

## Troubleshooting

### Port Already in Use

If you get a port conflict:
- Check if another instance is running: `lsof -i :8501` or `lsof -i :8502`
- Kill the process or use different ports in the scripts

### Database Connection Issues

- Verify `DATABASE_URL` in your `.env.development` file
- Ensure the development database exists
- Check database permissions

### Hot Reload Issues

- Production script has `--server.runOnSave false` to prevent unwanted reloads
- Development script has hot-reload enabled by default
- If issues occur, restart the app

### Branch Conflicts

If you get conflicts when switching branches:
- Commit or stash your changes first
- `git stash` to temporarily save changes
- `git stash pop` to restore after switching

## Best Practices

1. ✅ Always test in development before merging to main
2. ✅ Keep production and development databases separate
3. ✅ Use descriptive commit messages
4. ✅ Create feature branches from `development` for larger features
5. ✅ Regularly merge `main` into `development` to stay up to date

## Feature Branch Workflow (Optional)

For larger features, create feature branches:

```bash
# From development branch
git checkout development
git pull origin development
git checkout -b feature/new-feature

# Make changes, commit, push
git push origin feature/new-feature

# When ready, merge back to development
git checkout development
git merge feature/new-feature
git push origin development
```

