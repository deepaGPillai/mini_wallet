# Wallet-Manager
Django Project for Wallet Manager

How to Setup ?
1) pip install -r requirements.txt
2) Update the DB Settings in walletmanager/settings.py
   ```javascript
   DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'wallet',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': '127.0.0.1',
        'PORT': '5432'
    }}
3) Create Database in Postgres (wallet)
4) python manage.py makemigrations
5) python manage.py migrate
6) python manage.py runserver
