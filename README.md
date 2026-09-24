# Book Life

Book Life is a Django-based library management system. It supports user registration and login, role-based access, book catalog management, reservations, borrowing, returns, and scheduled email reminders.

The project is divided into three Django applications. `accounts` owns users and authentication, `books` owns books and lending records, and `base` provides shared dashboards and background tasks. The `main` package contains the project-wide settings, URL configuration, WSGI entry point, and Celery configuration.

## How It Works

1. A user registers with an email address and username, then signs in through the accounts pages.
2. Users receive permissions through the `MEMBER`, `LIBRARIAN`, or `ADMIN` groups.
3. Books track their total and available copies. A reservation or borrow operation updates availability through the application views.
4. Reservations have an expiry time. Borrows have a due date and can be returned or marked expired.
5. Celery tasks periodically check reservations and borrows. When configured with Redis and SMTP email settings, they can send reminders and expiry notifications.

The normal local workflow is: create the environment, install dependencies, apply migrations, create groups, create the development administrator, and start the Django server.

## Features

- Custom user model with email-based authentication
- User registration, login, and logout
- Role groups for `ADMIN`, `LIBRARIAN`, and `MEMBER`
- Book catalog with title, author, ISBN, category, copies, and images
- Book reservations and reservation expiry
- Book borrowing, due dates, returns, and overdue status
- Admin and member dashboards
- Celery tasks for reservation expiry and due-date reminders
- SQLite database for local development

## Requirements

- Python 3.13 or newer
- Poetry, or Python `venv` with pip
- Redis, only if Celery background tasks are required
- MongoDB is not required by the current settings; the active database is SQLite

Python is the runtime for Django. Poetry reads `pyproject.toml` and installs the exact versions recorded in `poetry.lock`. A virtual environment keeps these packages separate from other Python projects. Redis is a message broker used by Celery; it is not needed to display the Django site.

## Local Setup

Open PowerShell in the project directory:

```powershell
cd D:\project\Book-life
```

### Option 1: Poetry

Install Poetry if it is not already installed:

```powershell
py -m pip install poetry
```

This installs the Poetry command-line tool. Restart the terminal if Windows does not immediately find the `poetry` command.

Install the project dependencies:

```powershell
poetry install
```

This reads the project dependency list and lock file, creates or uses Poetry's environment, and installs Django, image support, Celery, Redis support, and the other packages.

Run the following commands through Poetry:

```powershell
poetry run python manage.py migrate
poetry run python manage.py group_setup
poetry run python manage.py admin_setup
poetry run python manage.py runserver
```

`poetry run` executes each command inside the environment created by Poetry. `migrate` creates the database tables. `group_setup` creates the default permission groups. `admin_setup` creates the predefined development administrator. `runserver` starts Django's development server.

### Option 2: Virtual environment

Create and activate a local virtual environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

The first command creates a project-local environment in `.venv`. The second activates it for the current PowerShell session. The `(.venv)` prefix in the terminal confirms that it is active.

Install the dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install django django-ajax-datatable celery redis python-dotenv pillow gunicorn
```

These commands update pip and install the packages needed to run the SQLite version of the application. `gunicorn` is included for Render; Django's development server is sufficient locally.

Initialize and run the application:

```powershell
python manage.py migrate
python manage.py group_setup
python manage.py admin_setup
python manage.py runserver
```

With the virtual environment active, `python` points to the environment's interpreter. These commands perform the same initialization as the Poetry workflow.

If PowerShell blocks activation, run this once for the current user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Open the Application

- Application: http://127.0.0.1:8000/
- Admin site: http://127.0.0.1:8000/admin/
- Login: http://127.0.0.1:8000/accounts/login/
- Registration: http://127.0.0.1:8000/accounts/register/
- Books: http://127.0.0.1:8000/books/list/

The trailing slash is part of each URL. Django serves the home page at `/`, authentication under `/accounts/`, and book-related pages under `/books/`. The admin site is a separate Django administration interface.

The `admin_setup` command creates this development administrator:

```text
Email: admin@gmail.com
Password: admin@123
```

Change this password before using the application outside local development.

## Useful Commands

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py test
python manage.py createsuperuser
```

`check` finds configuration problems without changing the database. `makemigrations` creates migration files after model changes, while `migrate` applies those files. `collectstatic` gathers CSS and other static files for deployment. `test` runs the automated tests. `createsuperuser` interactively creates another administrator.

The custom setup commands are:

```powershell
python manage.py group_setup
python manage.py admin_setup
```

`group_setup` is safe to run repeatedly: it creates missing groups and assigns their permissions. `admin_setup` creates the fixed development account only when it does not already exist.

## Environment Variables

Create a `.env` file in the project root for email configuration:

```env
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
```

`main/settings.py` loads this file with `python-dotenv`. The values configure SMTP, which is used by the Celery email tasks. Do not commit `.env` or real passwords; `.env` is ignored by Git.

The application currently uses Redis at `redis://127.0.0.1:6379/0` for Celery. Start Redis separately if scheduled background tasks or email tasks are needed.

## Celery Workers

With Redis running, start a Celery worker in one terminal:

```powershell
celery -A main worker --loglevel=info
```

Start Celery Beat in another terminal to run the scheduled tasks:

```powershell
celery -A main beat --loglevel=info
```

The worker consumes queued tasks from Redis. Beat is the scheduler that triggers the periodic tasks configured in `CELERY_BEAT_SCHEDULE`. Run each process in its own terminal. If Redis is unavailable, the web application can still start, but queued email and scheduled expiry processing will not work.

The Django web server can run without Celery, but task execution and scheduled reminders require both Redis and Celery processes.

## Database

The active configuration in `main/settings.py` uses SQLite:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

SQLite stores the entire development database in `db.sqlite3`, so no separate database server is required locally. Django creates this file when `migrate` is run. The file is intentionally ignored by Git because it contains local data rather than portable schema code.

`db.sqlite3` is ignored by Git. This is suitable for local development, but it is not durable storage for a production deployment on Render. Use a managed production database such as Render PostgreSQL, or configure MongoDB deliberately and update the Django models and settings for that backend.

The commented MongoDB configuration is not active. Installing `django-mongodb-backend` alone does not switch the project to MongoDB, and mixing the backend with the active SQLite configuration can cause Django system-check errors.

## Deploying to Render

Create a Render Web Service connected to this repository.

Render checks out the repository on a Linux server, runs the build command once during deployment, and runs the start command as the long-lived web process. The service must bind to `0.0.0.0` and use Render's `$PORT`; binding only to `127.0.0.1` would make the service unreachable from the internet.

### Build command

```bash
pip install poetry && poetry install --no-root && poetry run python manage.py collectstatic --noinput && poetry run python manage.py migrate
```

This installs Poetry, installs the locked project dependencies without trying to package the repository itself, collects static files without an interactive prompt, and creates the database schema. Run `group_setup` and `admin_setup` separately as a one-time deployment task if the deployed application needs those default records.

### Start command

```bash
poetry run gunicorn main.wsgi:application --bind 0.0.0.0:$PORT
```

Gunicorn is the production WSGI server. `main.wsgi:application` points Gunicorn to this project's WSGI application, and `$PORT` is supplied automatically by Render.

Add these Render environment variables before deploying:

```text
SECRET_KEY=<a-long-random-secret>
DEBUG=False
ALLOWED_HOSTS=<your-service-name>.onrender.com
```

`SECRET_KEY` signs sessions and other security-sensitive values. `DEBUG=False` disables development error pages. `ALLOWED_HOSTS` tells Django which host names it may serve. Never use the development secret key or expose email passwords in source control.

The current settings file contains development defaults and should be updated to read these values from the environment before production use. SQLite data can also be lost when a Render service is redeployed, so use persistent managed storage for real deployments.

## Project Structure

```text
accounts/    Custom user model, authentication, and setup commands
books/       Books, reservations, borrowing, forms, and views
base/        Dashboards, shared views, and Celery tasks
main/        Django settings, URL configuration, WSGI, and Celery app
templates/   HTML templates
static/      CSS and static assets
media/       Uploaded book images
manage.py    Django command-line utility
pyproject.toml  Project metadata and dependencies
```

## License

No license has been specified for this project yet.
