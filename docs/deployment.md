```markdown
# Развёртывание проекта

## Требования к серверу

- ОС: Ubuntu 22.04 LTS (рекомендуется) или аналогичная
- Python 3.13+
- PostgreSQL (рекомендуется) или SQLite (для разработки)
- Nginx (веб-сервер)
- Gunicorn (WSGI-сервер)
- Git

---

## Подготовка сервера

### 1. Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Установка необходимых пакетов

```bash
sudo apt install -y python3-pip python3-dev python3-venv nginx git postgresql postgresql-contrib libpq-dev
```

### 3. Создание пользователя для проекта (опционально)

```bash
sudo adduser --system --group --shell /bin/bash catalog
sudo su - catalog
```

---

## Установка проекта

### 4. Клонирование репозитория

```bash
git clone https://github.com/NetMann-git/django-catalog.git
cd django-catalog
```

### 5. Создание виртуального окружения и установка зависимостей

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 6. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```
SECRET_KEY=ваш-секретный-ключ
DEBUG=False
ALLOWED_HOSTS=ваш-домен.ru,www.ваш-домен.ru
DATABASE_URL=postgres://user:password@localhost:5432/dbname
```

### 7. Настройка базы данных (PostgreSQL)

Создайте базу данных и пользователя:

```bash
sudo -u postgres psql
CREATE DATABASE catalog_db;
CREATE USER catalog_user WITH PASSWORD 'ваш_пароль';
ALTER ROLE catalog_user SET client_encoding TO 'utf8';
ALTER ROLE catalog_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE catalog_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE catalog_db TO catalog_user;
\q
```

Обновите `DATABASE_URL` в `.env` соответственно.

### 8. Миграции и сбор статики

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 9. Создание суперпользователя

```bash
python manage.py createsuperuser
```

---

## Настройка Gunicorn

### 10. Создание systemd-сервиса для Gunicorn

Создайте файл `/etc/systemd/system/catalog.service`:

```
[Unit]
Description=Gunicorn instance for Django Catalog
After=network.target

[Service]
User=catalog
Group=catalog
WorkingDirectory=/home/catalog/django-catalog
Environment="PATH=/home/catalog/django-catalog/.venv/bin"
EnvironmentFile=/home/catalog/django-catalog/.env
ExecStart=/home/catalog/django-catalog/.venv/bin/gunicorn --workers 3 --bind unix:catalog.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Запустите и включите службу:

```bash
sudo systemctl start catalog
sudo systemctl enable catalog
```

---

## Настройка Nginx

### 11. Создание конфигурации Nginx

Создайте файл `/etc/nginx/sites-available/catalog`:

```
server {
    listen 80;
    server_name ваш-домен.ru www.ваш-домен.ru;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/catalog/django-catalog;
    }
    location /media/ {
        root /home/catalog/django-catalog;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/catalog/django-catalog/catalog.sock;
    }
}
```

Активируйте сайт и перезагрузите Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/catalog /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

---

## Настройка SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d ваш-домен.ru -d www.ваш-домен.ru
```

---

## Обновление проекта

При обновлении кода выполните:

```bash
cd /home/catalog/django-catalog
git pull
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart catalog
```

---

## Проверка

Откройте браузер и перейдите на `https://ваш-домен.ru`. Сайт должен работать.

---

## Устранение неполадок

- Проверьте логи Gunicorn: `sudo journalctl -u catalog`
- Проверьте логи Nginx: `sudo tail -f /var/log/nginx/error.log`
- Проверьте доступность сокета: `ls -la /home/catalog/django-catalog/catalog.sock`


---
text

## 📋 Что изменено:

| Что было | Что стало |
|----------|-----------|
| `wedding-salon-site` | `django-catalog` |
| `wedding_db` | `catalog_db` |
| `wedding_user` | `catalog_user` |
| `wedding.service` | `catalog.service` |
| `wedding.sock` | `catalog.sock` |
| Пользователь `wedding` | Пользователь `catalog` |

```