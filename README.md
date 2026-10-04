# Food Delivery System

A responsive restaurant and food-delivery application built with Django templates, Bootstrap 5 and MySQL. Customers can register, search a menu, manage a session cart, check out with cash on delivery, and follow their orders. Staff use a purpose-built dashboard at `/manage/`, alongside Django Admin at `/admin/`.

## Features

- Home, menu, meal detail, about, contact, login, registration, dashboard, cart, checkout, order confirmation, order history/detail and profile pages.
- Username/email login using Django's authentication and password hashing; registration checks duplicate email and Django password rules.
- MySQL-backed category and food catalog, keyword search, category filtering and price sorting.
- Session cart with add, update, remove, duplicate-item quantity accumulation and availability checks.
- Transactional checkout; locked availability recheck, purchase-time prices, private order views, and cash-on-delivery only.
- Responsive restaurant dashboard with order, food, category, user, website-content and reporting pages.
- Staff-only access checks; only superusers can grant staff dashboard access. Customer accounts cannot open management pages.
- Dashboard statistics from the database, recent orders/users, order status summary, actual ordered-item popularity and delivered-order revenue.
- Food/category CRUD with image upload, search, filters, featured/popular food controls, homepage category visibility and safe delete confirmations.
- Order search/date/status filters, complete details and staff status updates.
- User search, account activation and order history; passwords are never displayed or edited in this dashboard.
- Homepage promotion editor and active category/featured-food controls connected to the same catalog models.
- Django Admin remains available for site settings and direct model administration.
- Idempotent `seed_food` management command and Django tests.

## Technology and requirements

Python 3.10+, Django 5.1+, MySQL 8+, `mysqlclient`, Pillow and python-dotenv. No React, Node.js, MongoDB, or online payment package is used. Bootstrap and its JS bundle are loaded from jsDelivr in templates.

## Install

From this directory:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

On macOS/Linux, activate with `source venv/bin/activate` and copy `.env.example` to `.env`.

## MySQL setup

Create a database and a least-privilege local application account (replace the example password):

```sql
CREATE DATABASE food_delivery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'food_app'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
GRANT ALL PRIVILEGES ON food_delivery.* TO 'food_app'@'localhost';
FLUSH PRIVILEGES;
```

Put the matching database name, user, password, host, port and a newly generated `SECRET_KEY` in `.env`. If `DEBUG` is omitted, the built-in `runserver` command enables development mode so local static/media files work; other commands and deployed WSGI/ASGI processes remain `DEBUG=False`. An explicit `.env` or environment value always takes precedence. Local loopback hostnames (`localhost`, `127.0.0.1`, and `[::1]`) are allowed for development or when no host list is configured; there is no wildcard. For deployment set `DEBUG=False` and add only your public hostnames to `ALLOWED_HOSTS`; with production hostnames configured, only those names are accepted. The app uses SQLite only when `DB_NAME` is unset, which is convenient for local checks; setting it selects MySQL.

## Migrate and run

```powershell
python manage.py makemigrations food
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_food
python manage.py runserver
```

Open http://127.0.0.1:8000/ for the customer storefront, http://127.0.0.1:8000/manage/ for the custom restaurant dashboard, and http://127.0.0.1:8000/admin/ for Django Admin. Sign into `/manage/` using a Django user with `is_staff=True`; create the owner account with `createsuperuser`. Uploaded food, category and hero images are stored under `media/` via `MEDIA_ROOT`; development media serving is enabled only in DEBUG. Static assets are in `food/static/food/` and `static/` is the collected-static source.

## Tests

```powershell
python manage.py test
python manage.py check
```

The tests cover registration/login, menu search and details, cart changes, checkout/order totals, order privacy, staff-only access, dashboard pages, food/category CRUD, deletion protection, order status updates, staff-permission boundaries, homepage content, and image uploads. Run them with a reachable MySQL database for the production database backend, or leave `DB_NAME` unset to use SQLite.

## Structure

```text
food_delivery/
├── manage.py
├── food_delivery/              # settings, root URLs, WSGI/ASGI
├── food/                       # models, forms, views, URLs, admin, tests
│   ├── management/commands/    # seed_food
│   ├── templates/food/         # storefront, account and custom staff dashboard
│   ├── staff_views.py          # staff-only dashboard and management actions
│   ├── staff_urls.py           # /manage/ route map
│   └── static/food/            # storefront and dashboard CSS, JavaScript, artwork
├── templates/base.html
├── media/                      # user uploads at runtime
├── requirements.txt
└── .env.example
```

## Main data models

- `FoodCategory`: catalog category and optional image.
- `FoodItem`: category, description, price, optional image and availability.
- `SiteContent`: editable homepage heading, subheading and hero image.
- `UserProfile`: contact number linked one-to-one with Django's user.
- `Order`: owner, delivery/contact details, total, date and status.
- `OrderItem`: quantity and price snapshot for an item at checkout.

## Notes

Keep `.env` and uploaded customer data out of version control. `SECRET_KEY` has a development fallback solely so the project can show a helpful startup configuration; replace it in `.env` and never use the fallback in production. Set up HTTPS and secure cookie settings when deploying. Contact page is informational; order questions can be followed through the account order history.
