# Migration History Fix for Django Sites

## Problem
The error occurs because:
1. `allauth` migrations were applied before `django.contrib.sites` was added to INSTALLED_APPS
2. `allauth` depends on `sites` framework, but sites migrations weren't run first
3. Django detects this inconsistency and prevents further migrations

## Solution Options

### Option 1: Reset Migration History (Recommended for Development)

**⚠️ WARNING: This will lose migration history but preserve data**

```bash
# 1. Fake unapply the problematic migrations
python3 manage.py migrate socialaccount 0001 --fake
python3 manage.py migrate account 0001 --fake

# 2. Run sites migrations first
python3 manage.py migrate sites

# 3. Re-apply allauth migrations
python3 manage.py migrate account
python3 manage.py migrate socialaccount

# 4. Run all remaining migrations
python3 manage.py migrate
```

### Option 2: Manual Database Fix (If Option 1 doesn't work)

```bash
# 1. Mark sites migration as applied (since tables might already exist)
python3 manage.py migrate sites --fake-initial

# 2. Run remaining migrations
python3 manage.py migrate
```

### Option 3: Nuclear Option (Last Resort - Development Only)

**⚠️ WARNING: This will delete ALL migration history and data**

```bash
# 1. Delete migration files (keep __init__.py files)
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# 2. Delete database (if using SQLite) or drop/recreate MySQL database
# For MySQL:
# mysql -u root -p -e "DROP DATABASE your_db_name; CREATE DATABASE your_db_name;"

# 3. Create fresh migrations
python3 manage.py makemigrations
python3 manage.py migrate
```

## Recommended Steps for Your Case

Since you're in development, try **Option 1** first:

```bash
# Step 1: Fake unapply allauth migrations
python3 manage.py migrate socialaccount 0001 --fake
python3 manage.py migrate account 0001 --fake

# Step 2: Apply sites migrations
python3 manage.py migrate sites

# Step 3: Re-apply allauth migrations
python3 manage.py migrate account
python3 manage.py migrate socialaccount

# Step 4: Apply all remaining migrations
python3 manage.py migrate

# Step 5: Verify everything is working
python3 manage.py validate_google_oauth
```

## After Fixing Migrations

1. **Create Site object:**
```bash
python3 manage.py shell -c "
from django.contrib.sites.models import Site
site, created = Site.objects.get_or_create(pk=1)
site.domain = 'localhost:8000'
site.name = 'Angaar Batch Portal'
site.save()
print(f'Site configured: {site.domain}')
"
```

2. **Test Google OAuth:**
```bash
python3 manage.py validate_google_oauth
```

## Prevention for Future

Always add `django.contrib.sites` to INSTALLED_APPS before adding allauth to avoid this issue.

The correct order in INSTALLED_APPS should be:
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Add this BEFORE allauth
    
    # Your apps
    'accounts.apps.AccountsConfig',
    # ... other apps
    
    # Third party apps
    'allauth',  # Sites should come before this
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]
```
