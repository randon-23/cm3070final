# CM3070 Final Project
Volontera - The Volunteering Social and Management Platform
<br>
**NOTE:** JUST IN CASE, when accessing deployed site on *https://volontera.fly.dev/*, if you are initially met with a 502 Bad Gateway error emanating from NGINX, this is due to the machine having been in idle and is still booting up. Simply refresh once/twice and eventually the site will load. 
<br>
**NOTE:** The *prod* branch was used for deployment whilst *dev* was used for local development. I recommend cloning the *dev* branch if you're planning to run the application locally.

# Prerequisites:
- Development was doen on Windows 11 OS
- Python 3.11 installed
- PostgreSQL
- Node.js installed (v14.0 or later)
- npm or yarn
- Windows Subsystem for Lunux (WSL) for Redis set up (This was done by installing Ubuntu for Windows from Microsoft Store)

# Python/Django setup
Create a virtual environment to isolate all project dependencies which are going to be installed
Once the virtual env is set up using 
```bash
python -m venv your_venv_name
```
To activate the venv on Windows, use command:
```bash
.\your_venv_name\Scripts\Activate.ps1
```
All project dependencies will be installed from the requirements.txt file via
```bash
pip install -r requirements.txt
```
# Environment file (.env)
Set up a .env file in the cloned project with the following environment variables:
```env
EMAIL_HOST_USER=volonteracm3070@gmail.com
EMAIL_HOST_PASSWORD=ayps uewo gujl lnwi
DJANGO_ENV=development
DJANGO_SECRET_KEY="django-insecure-5bhh%kjha59o@vfj&26m8e&iv!4+nj_)x&oam^ty=45d47oihi"
GOOGLE_API_KEY=AIzaSyA29sFn-7vH4j5JSlu89gQ86QUdvjHbCCA
GOOGLE_PLACES_API_KEY=AIzaSyA29sFn-7vH4j5JSlu89gQ86QUdvjHbCCA
# Placeholders when in development, will be overwritten in production .env
REDIS_HOST=127.0.0.1
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
```

# Node.js setip
Ensure Node.js and npm are installed. Once Node.js installed, run command
```bash
npm install
```
to install all node dependencies/modules associated with Tailwind

# Redis setup for Windows (using WSL for Redis server)
To install redis on the newly installed Ubuntu for Windows, the redis-server is installed within the Linux distribution.
Run
```bash
sudo apt udpate
apt list --upgradable
sudo apt upgrade
```
After these default packages are installed and updated in the Linux distribution, then redis-server installed
```bash
sudo apt install redis-server
```
Redis server is then started by running:
```bash
sudo service redis-server start
```
To ensure the service is running:
```bash
redis-cli ping
```
To ensure Redis starts automatically with the WSL Linux distribution instance, pass the
command:
```bash
sudo systemctl enable redis-server.service
```

# Migrations and database set up
Install PostgreSQL from the official site: https://www.postgresql.org/download/
If in Linux:

Access PostgreSQL from command line:
```bash
psql -U postgres -d postgres
```

Create a new database and user:
```sql
CREATE DATABASE volontera_db;
CREATE USER volontera_user WITH PASSWORD 'your_secure_password';
ALTER ROLE volontera_user SET client_encoding TO 'utf8';
ALTER ROLE volontera_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE volontera_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE volontera_db TO volontera_user;
\q
```
Make sure to replace the DB credentials in your .env file or settings/dev.py file as needed:
Example:
```bash
DB_NAME=volontera_db
DB_USER=volontera_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
```

After configurations, apply migrations using Django:
```bash
python manage.py makemigrations
python manage.py migrate
```

and create a superuser to access the Django admin:
```bash
python manage.py createsuperuser
```

Running the server locally:
```bash
python manage.py runserver
```
This will start a development server which serves the Django project along with an ASGI Daphne routing implementation for websocket functionality

# Running celery app
We also need to run the messaging/queueing service 'Celery'. This is done by activating Celery in a sperate terminal to handle background tasks via:
```bash
celery --app=volontera.celery:app worker --loglevel=INFO --pool=solo
```
