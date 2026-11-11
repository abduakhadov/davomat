# Davomat - Yuz orqali davomat tizimi (1-bosqich)

Ushbu loyiha xodimlarning ishga kelib-ketishini yuz orqali belgilash tizimining 1-bosqichi: ro'yxatdan o'tish, login, profil, rasm yuklash va admin tasdig'i.

## Texnologiyalar
- Python 3.12
- Django 5.2 LTS
- PostgreSQL 16
- Pillow, psycopg 3, django-environ

## Loyihani ishga tushirish

### 1. Ma'lumotlar bazasini Docker orqali ko'tarish
```bash
docker compose up -d
```

### 2. Virtual muhitni yaratish va faollashtirish
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 3. Bog'liqliklarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. Muhit o'zgaruvchilarini sozlash
```bash
cp .env.example .env
```
Zarur bo'lsa `.env` faylidagi sozlamalarni tahrirlang.

### 5. Migratsiyalarni qo'llash
```bash
python manage.py migrate
```

### 6. Admin (superuser) yaratish
```bash
python manage.py createsuperuser
```

### 7. Serverni ishga tushirish
```bash
python manage.py runserver
```

Brauzerda ochish: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Testlar va kod sifati
```bash
ruff check .
pytest
```

