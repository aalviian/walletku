# Walletku APIs

This project implements Wallet APIs Collection.

Requires Python 3.

### Run The Project
1. Clone this repository
2. Setup the database, e.g below.
```csharp
{
    'ENGINE': 'django.db.backends.mysql',
    'HOST': '127.0.0.1',
    'NAME': 'walletku',
    'USER': 'root',
    'PASSWORD': '',
    'CONN_MAX_AGE': 0
}
```
3. At the root directory, run below command:
```csharp
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
4. See the API Documentation.
http://localhost:8000/api/v1/docs/


### Before committing code
- Run `pytest`
- Run `flake8 .`
**NOTE**: You can run `flake8` command for specific directory.
