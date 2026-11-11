# Davomat tizimi: 1-bosqich vazifasi

Bu hujjat o'z-o'zicha yetarli: 1-bosqichni boshlash uchun boshqa narsa o'qish shart emas.
Hujjatda yozilmagan yoki noaniq joy chiqsa, taxmin qilmang, Ibrohimdan so'rang.

«Davomat» (`davomat`) vaqtinchalik nom.

## 1. Loyiha nima qiladi

Xodim saytga kiradi va «Tasdiqlash» tugmasini bosadi. Kamera ochiladi, tizim yuzni profildagi
rasm bilan solishtiradi va ishga keldi yoki ketdi deb bazaga yozadi. Oxirgi amal kirish bo'lsa,
yangisi chiqish bo'ladi, aks holda kirish.

Butun loyiha 6 bosqichdan iborat:

| # | Bosqich |
|---|---------|
| **1** | **Ro'yxatdan o'tish, login, profil, rasm yuklash, admin tasdig'i (shu hujjat)** |
| 2 | Yuz tanish moduli, o'xshashlik chegarasini real rasmlarda o'lchash |
| 3 | Kamera sahifasi, solishtirish, kirish/chiqish mantig'i |
| 4 | Himoya: tirik odam tekshiruvi, ofis IP tekshiruvi, urinishlar cheklovi |
| 5 | Hisobot: bugun kim ishda, tarix, Excel eksport, adminning tuzatishi |
| 6 | Docker va HTTPS bilan serverga chiqarish, jamoada sinash |

## 2. 1-bosqich maqsadi

Bosqich oxirida quyidagi zanjir ishlashi kerak:

1. Yangi odam ro'yxatdan o'tadi va tizimga kiradi.
2. Profiliga o'z rasmini yuklaydi va rozilik belgisini qo'yadi.
3. Admin rasmni ko'radi, tasdiqlaydi yoki sababini yozib rad etadi.
4. Foydalanuvchi rasm holatini profilida ko'radi.
5. Rasmni faqat uning egasi va admin ko'ra oladi.

**Nega admin tasdig'i kerak.** Ali profiliga Valining rasmini qo'ysa, keyin Vali uning o'rniga
davomat belgilab bera oladi. Shuning uchun rasmni admin ko'zdan kechiradi va tasdiqlangan rasmni
foydalanuvchi o'zi o'zgartira olmaydi.

### Bu bosqichga kirmaydi

Quyidagilarni hozir qilmang, ular uchun alohida bosqich bor:

- Yuzni avtomatik aniqlash va embedding olish (2-bosqich). Hozircha rasmni faqat admin tekshiradi.
- Kamera, «Tasdiqlash» tugmasi, kirish/chiqish yozuvlari (3-bosqich).
- Tirik odam tekshiruvi, IP tekshiruvi, login urinishlarini cheklash (4-bosqich).
- Hisobotlar va Excel (5-bosqich).
- Django'ni Docker'ga joylash, HTTPS, server, ochiq ro'yxatdan o'tishni cheklash (6-bosqich).
- Parolni email orqali tiklash. Parolni admin panelda admin yangilaydi.

## 3. Texnologiyalar

- Python 3.12
- Django 5.2 LTS
- PostgreSQL 16 (ishlab chiqishda Docker'da)
- `psycopg[binary]` (3-versiya), `Pillow`, `django-environ`
- Django shablonlari va Bootstrap 5. React yoki alohida frontend yo'q.
- Sifat: `ruff`, `pytest`, `pytest-django`

## 4. Loyiha tuzilishi

```
davomat/
  manage.py
  requirements.txt
  docker-compose.yml      # faqat postgres
  .env.example
  .gitignore              # .env, .venv, private_media/, __pycache__/
  README.md               # noldan ishga tushirish tartibi
  config/                 # settings, urls, wsgi
  accounts/               # User modeli, ro'yxatdan o'tish, login, profil
  faces/
    models.py             # FaceTemplate
    services.py           # holatni o'zgartiradigan yagona joy
    images.py             # rasmni tekshirish va tozalash
    storage.py            # yopiq saqlash
    forms.py
    views.py
    urls.py
    admin.py
    tests/
  templates/
  static/
  private_media/          # gitga kirmaydi
```

`attendance` ilovasi 3-bosqichda qo'shiladi, hozir ochmang.

## 5. Sozlamalar

`.env.example`:

```
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://davomat:davomat@localhost:5432/davomat
PRIVATE_MEDIA_ROOT=./private_media
```

`settings.py` talablari:

- `AUTH_USER_MODEL = "accounts.User"`. **Birinchi `migrate`dan oldin** qo'yiladi, keyin almashtirish juda og'ir.
- `LANGUAGE_CODE = "uz"`, `TIME_ZONE = "Asia/Tashkent"`, `USE_TZ = True`.
- `LOGIN_URL = "/login/"`, `LOGIN_REDIRECT_URL = "/profile/"`, `LOGOUT_REDIRECT_URL = "/login/"`.
- Django'ning 4 ta standart parol validatori yoqilgan.
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, baza manzili faqat `.env`dan o'qiladi.
- Rasm cheklovlari sozlamada turadi: `FACE_MAX_UPLOAD_BYTES = 10 * 1024 * 1024`, `FACE_MIN_SIDE = 400`,
  `FACE_MAX_SIDE = 1600`, `FACE_MAX_PIXELS = 50_000_000`.
- `urls.py`da `static(settings.MEDIA_URL, ...)` **bo'lmaydi**: yuz rasmlari ochiq manzildan berilmaydi.

`docker-compose.yml`: bitta `postgres:16` servisi, `127.0.0.1:5432` portida, ma'lumot `volume`da.

## 6. Ma'lumotlar modeli

### `accounts.User` (`AbstractUser`dan)

- `username`: 3–30 belgi, faqat kichik lotin harflari, raqam va `_`. Doim kichik harfda saqlanadi,
  login formasi ham kiritilganni kichik harfga o'tkazadi (`Ali` va `ali` bitta foydalanuvchi).
  `createsuperuser` ham shu qoidaga bo'ysunadi.
- `first_name`, `last_name`: majburiy, 50 belgigacha.
- `REQUIRED_FIELDS = ["first_name", "last_name"]`.
- Admin: `is_staff=True`.

Email va telefon yig'ilmaydi: ishga kerak bo'lmagan shaxsiy ma'lumot olinmaydi.

### `faces.FaceTemplate`

| Maydon | Turi | Izoh |
|--------|------|------|
| `id` | UUID, PK | Manzilda ketma-ket raqam ko'rinmasin |
| `user` | FK `User`, CASCADE | `related_name="face_templates"` |
| `image` | ImageField, `blank=True`, yopiq storage | Rad etilganda fayl o'chiriladi |
| `status` | `pending` / `approved` / `rejected` | Standart `pending` |
| `consent_at` | DateTime | Rozilik vaqti, majburiy |
| `rejection_reason` | Text, `blank=True` | Rad etilganda to'ldiriladi |
| `reviewed_by` | FK `User`, SET_NULL, `null=True` | `related_name="+"` |
| `reviewed_at` | DateTime, `null=True` | |
| `embedding` | BinaryField, `null=True` | Hozir bo'sh, 2-bosqichda to'ldiriladi |
| `model_name` | Char(50), `blank=True` | Hozir bo'sh, 2-bosqichda to'ldiriladi |
| `created_at` | DateTime, `auto_now_add` | |

Cheklov (bazada):

```python
UniqueConstraint(
    fields=["user"],
    condition=Q(status__in=["pending", "approved"]),
    name="one_live_face_per_user",
)
```

Bitta foydalanuvchida bir vaqtda ko'pi bilan bitta `pending` yoki `approved` rasm bo'ladi.
`OneToOne` emas, `FK` olinishining sababi: rad etilganlar tarixi saqlanadi, keyinchalik bir odamga
bir nechta rasm kerak bo'lsa, faqat shu cheklovni olib tashlash yetadi.

**Joriy rasm** deb foydalanuvchining `created_at` bo'yicha eng oxirgi yozuvi olinadi.

## 7. Rasm holatlari

```
(rasm yo'q) --yuklash--> PENDING --admin tasdiqlaydi--> APPROVED
                            |                              |
                            | admin rad etadi              | admin bekor qiladi
                            v                              |
                         REJECTED <------------------------+

REJECTED --yangi rasm yuklash--> yangi yozuv, PENDING
```

- Ruxsat etilgan o'tishlar faqat shular: `pending` dan `approved`ga, `pending` dan `rejected`ga,
  `approved` dan `rejected`ga. Qolganlari xato beradi.
- Foydalanuvchi yangi rasmni faqat ikki holatda yuklay oladi: rasmi umuman yo'q yoki joriy rasmi `rejected`.
- Admin tasdiqlangan rasmni bekor qilsa (masalan, odam rasmini yangilamoqchi), bu `rejected` bilan
  bir xil ishlaydi va foydalanuvchi yangisini yuklay oladi.

Holatni **faqat** `faces/services.py`dagi funksiyalar o'zgartiradi:

- `submit_photo(user, uploaded_file) -> FaceTemplate`
- `approve(template, reviewer)`: `reviewed_by` va `reviewed_at`ni to'ldiradi.
- `reject(template, reviewer, reason)`: sabab bo'sh bo'lsa xato; `reviewed_by`, `reviewed_at`ni to'ldiradi,
  rasm faylini o'chiradi.

`approve` va `reject` yozuvni `select_for_update` bilan qulflab ishlaydi, ikki admin bir vaqtda bossa ham holat buzilmaydi.

## 8. Sahifalar

| Manzil | Metod | Kim uchun | Nima qiladi |
|--------|-------|-----------|-------------|
| `/` | GET | hamma | Login bo'lsa `/profile/`, aks holda `/login/`ga yuboradi |
| `/register/` | GET, POST | mehmon | Ro'yxatdan o'tish |
| `/login/` | GET, POST | mehmon | Tizimga kirish |
| `/logout/` | POST | login bo'lgan | Chiqish (Django 5'da faqat POST) |
| `/profile/` | GET | login bo'lgan | Ism, rasm, holat |
| `/profile/photo/` | GET, POST | login bo'lgan | Rasm yuklash formasi |
| `/faces/<uuid>/image/` | GET | egasi yoki admin | Rasmning o'zi |
| `/admin/` | | `is_staff` | Admin panel |

Login bo'lgan odam `/register/` yoki `/login/`ga kirsa, `/profile/`ga yuboriladi.

**Ro'yxatdan o'tish formasi:** Ism, Familiya, Login, Parol, Parolni takrorlang.
Muvaffaqiyatli bo'lsa, foydalanuvchi avtomatik kiradi va `/profile/`ga o'tadi.

**Rasm yuklash formasi:**

- Fayl tanlash: `accept="image/jpeg,image/png"`.
- Rozilik belgisi (standart holatda belgilanmagan, majburiy).
- Ko'rsatma matni (12-bo'limda).
- Muvaffaqiyatli bo'lsa, `/profile/`ga yo'naltiradi. Holat yuklash mumkin bo'lmaganda sahifa ham
  `/profile/`ga xabar bilan qaytaradi.

**Profil sahifasi:**

| Joriy holat | Foydalanuvchi ko'radi | «Rasm yuklash» tugmasi |
|-------------|-----------------------|------------------------|
| Rasm yo'q | «Rasm yuklanmagan» | bor |
| `pending` | Rasm va «Admin tekshirmoqda» | yo'q |
| `approved` | Rasm va «Tasdiqlangan» | yo'q |
| `rejected` | «Rad etilgan» va sabab | bor |

Hamma sahifa telefonda ham qulay bo'lsin: foydalanuvchilar asosan telefondan kiradi.

## 9. Rasmni qabul qilish tartibi

`faces/images.py`, tartib muhim:

1. Fayl hajmi `FACE_MAX_UPLOAD_BYTES`dan katta bo'lsa, rad etiladi.
2. `Image.open(fayl, formats=["JPEG", "PNG"])`. Turi fayl mazmunidan aniqlanadi, kengaytma va
   `Content-Type`ga ishonilmaydi.
3. Kenglik × balandlik `FACE_MAX_PIXELS`dan katta bo'lsa, rasm ochilmasdan rad etiladi (dekompressiya bombasi).
4. Rasm to'liq o'qiladi. `UnidentifiedImageError`, `OSError`, `DecompressionBombError` kabi xatolar
   forma xatosiga aylanadi, **500 sahifa chiqmasligi kerak**.
5. `ImageOps.exif_transpose`: telefon rasmlari aks holda yonboshlab qoladi va 2-bosqichda yuz topilmaydi.
6. Kichik tomoni `FACE_MIN_SIDE`dan kam bo'lsa, rad etiladi.
7. RGB'ga o'tkaziladi, shaffof fon oq bilan to'ldiriladi.
8. Uzun tomoni `FACE_MAX_SIDE`dan katta bo'lsa, proporsiya saqlangan holda kichraytiriladi.
9. JPEG (quality 90) sifatida, **EXIF'siz** saqlanadi: EXIF ichida GPS joylashuvi bo'lishi mumkin.
10. Fayl yo'li: `faces/<user_id>/<uuid4>.jpg`. Yuklangan fayl nomi hech qayerda ishlatilmaydi.

`submit_photo` bitta tranzaksiyada ishlaydi:

1. Foydalanuvchi qatorini `select_for_update` bilan qulflaydi.
2. Yuklash mumkinligini tekshiradi (7-bo'lim).
3. `FaceTemplate` yaratadi, `consent_at`ga hozirgi vaqtni yozadi.

Ikki marta bosilganda ikkinchi so'rov qulfdan keyin «allaqachon yuborilgan» holatini ko'radi.
Bazadagi cheklov oxirgi himoya sifatida qoladi; `IntegrityError` chiqsa ham 500 bo'lmasin.

## 10. Rasmlarni himoya qilish

Yuz rasmi biometrik ma'lumot, shuning uchun bu bo'lim majburiy.

- **Yopiq saqlash.** `faces/storage.py`da `FileSystemStorage(location=PRIVATE_MEDIA_ROOT, base_url=None)`
  qaytaradigan **funksiya** yoziladi va `ImageField(storage=shu_funksiya)` ga beriladi.
  Funksiya bo'lgani uchun mutlaq yo'l migratsiyaga tushmaydi va testda vaqtinchalik papkaga almashtirish oson.
- **Ko'rish.** `/faces/<uuid>/image/`:
  - mehmon `/login/`ga yuboriladi;
  - egasi yoki `is_staff` rasmni oladi;
  - boshqa foydalanuvchi **404** oladi (403 emas, rasm borligi ham bilinmasin);
  - sarlavhalar: `Content-Type: image/jpeg`, `Cache-Control: private, no-store`, `X-Content-Type-Options: nosniff`.
- **Faylni o'chirish.** Django faylni o'zi o'chirmaydi:
  - `reject` faylni o'chiradi va `image`ni bo'shatadi (begona odam rasmi bo'lishi mumkin, saqlanmaydi);
  - `FaceTemplate` o'chganda `post_delete` signali faylni o'chiradi, foydalanuvchi o'chganda ham shu ishlaydi;
  - fayl tranzaksiya muvaffaqiyatli tugagach o'chiriladi (`transaction.on_commit`).
- **Rasmlar tizimdan tashqariga chiqmaydi.** Real yuz rasmlari gitga, Telegram guruhga yoki loglarga tushmaydi.
  Testlardagi rasmlar kod ichida Pillow bilan yasaladi.

## 11. Admin panel

**`User`:** Django'ning `UserAdmin`idan meros oladi, parolni shu yerda yangilash mumkin.

**`FaceTemplate` ro'yxati:**

- Ustunlar: kichik rasm, ism-familiya, holat, yuklangan vaqt, kim tekshirgan, qachon.
- Filtr: holat. Qidiruv: login, ism, familiya. Tartib: yangilari tepada.
- Amal: «Tanlanganlarni tasdiqlash». Faqat `pending`larga ta'sir qiladi, qolganlari o'tkazib yuboriladi va bu haqda xabar chiqadi.

**`FaceTemplate` sahifasi:**

- Rasm katta ko'rinadi.
- Barcha maydonlar faqat o'qish uchun. Holatni qo'lda tahrirlash yo'q.
- Tugmalar: «Tasdiqlash» (`pending`da), «Rad etish» (`pending`da), «Bekor qilish» (`approved`da).
  Rad etish va bekor qilishda sabab majburiy.
- Tugmalar `services.py` funksiyalarini chaqiradi; `get_urls` orqali qo'shilgan view'lar POST, CSRF va
  `has_change_permission` bilan himoyalanadi.

Eslatmalar:

- `has_add_permission = False`: admin birovning nomidan rasm yuklamaydi, chunki rozilikni odamning o'zi beradi.
- Storage'da `base_url=None`, shuning uchun `.url` xato beradi. `image` maydoni admin formasida standart
  ko'rinishda chiqarilmaydi, rasm `/faces/<uuid>/image/` manzili orqali `<img>` bilan ko'rsatiladi.
- Rad etilgan yozuvda rasm yo'q, kichik rasm o'rnida «—» chiqadi.

## 12. Foydalanuvchi ko'radigan matnlar

**Ko'rsatma:**
«Yuzingiz to'liq va aniq ko'rinsin. Kadrda faqat siz bo'ling. Yuzni to'sadigan narsa (quyuq ko'zoynak, niqob) bo'lmasin. Yorug' joyda oling.»

**Rozilik:**
«Yuz rasmim ishga kelib-ketishni belgilash uchun ishlatilishiga va tizimda saqlanishiga roziman.»
Tizim real kompaniyada ishlatilsa, bu matn huquqshunos bilan kelishiladi.

**Xatolar:**

- «Faqat JPEG yoki PNG rasm yuklang.»
- «Rasm hajmi 10 MB dan oshmasin.»
- «Rasm juda kichik: kamida 400×400 piksel bo'lsin.»
- «Rasm juda katta o'lchamda. Boshqa rasm tanlang.»
- «Rasmni o'qib bo'lmadi. Boshqa fayl tanlang.»
- «Davom etish uchun rozilik belgisini qo'ying.»
- «Rasmingiz tekshirilmoqda, hozir yangisini yuklab bo'lmaydi.»
- «Rasmingiz tasdiqlangan. O'zgartirish uchun adminga murojaat qiling.»

## 13. Vazifalar

**Tartib:** T1 va T2 ni bitta odam birinchi bo'lib tugatib `main`ga qo'shadi, chunki boshqa hamma narsa
`User` modeli va birinchi migratsiyaga bog'liq. T3 va T4 keyin parallel ketadi. T5, T6, T7 esa T4 tugagach parallel ketadi.

### T1. Loyiha poydevori

Repo, `requirements.txt`, `config/`, `.env.example`, `.gitignore`, `docker-compose.yml`, `ruff`, `pytest`, `README.md`, 5-bo'limdagi sozlamalar.

*Tayyor:* yangi klon README bo'yicha ishga tushadi, `ruff check .` va `pytest` xatosiz o'tadi.

### T2. `User` modeli

`accounts` ilovasi, 6-bo'limdagi `User`, birinchi migratsiya, admin'da ro'yxatdan o'tkazish.

*Tayyor:* `createsuperuser` ishlaydi, admin panelga kiradi, username kichik harfda saqlanadi.

### T3. Ro'yxatdan o'tish, login, logout

Formalar, view'lar, `base.html`, sahifalar telefonga mos. 8-bo'lim.

*Tayyor:* yangi odam ro'yxatdan o'tib `/profile/`ga tushadi, chiqib qayta kira oladi.

### T4. `FaceTemplate` va servislar

Model, cheklov, yopiq storage, `submit_photo`, `approve`, `reject`, faylni o'chirish signali. 6, 7, 10-bo'limlar.

*Tayyor:* 7-bo'limdagi o'tishlar testlar bilan tasdiqlangan.

### T5. Rasm yuklash

`images.py`, forma, `/profile/photo/`. 9 va 12-bo'limlar.

*Tayyor:* 14-bo'limdagi «Rasm yuklash» testlari o'tadi.

### T6. Profil va rasmni ko'rish

`/profile/` to'rtta holati bilan, `/faces/<uuid>/image/`. 8 va 10-bo'limlar.

*Tayyor:* 14-bo'limdagi «Ruxsatlar» testlari o'tadi.

### T7. Admin panel

11-bo'lim to'liq.

*Tayyor:* admin ro'yxatdan rasmni ko'rib tasdiqlaydi, rad etadi, bekor qiladi.

### T8. Yakuniy tekshiruv

Qolgan testlar, 15-bo'limdagi ssenariy (kompyuter va telefonda), README'ni oxirgi holatga keltirish.

## 14. Majburiy testlar

**Ro'yxatdan o'tish**

- [ ] To'g'ri ma'lumot bilan foydalanuvchi yaratiladi va tizimga kiradi
- [ ] `Ali` bo'lsa, `ali` bilan ikkinchi marta o'tib bo'lmaydi
- [ ] Zaif parol va mos kelmagan parollar rad etiladi
- [ ] Ism yoki familiya bo'sh bo'lsa, rad etiladi
- [ ] Login bo'lgan odam `/register/`dan `/profile/`ga yuboriladi

**Rasm yuklash**

- [ ] JPEG qabul qilinadi
- [ ] Shaffof fonli PNG qabul qilinadi va JPEG'ga o'tadi
- [ ] GIF rad etiladi
- [ ] `.jpg` nomli matn fayli rad etiladi, 500 chiqmaydi
- [ ] Yarmi kesilgan JPEG rad etiladi, 500 chiqmaydi
- [ ] 10 MB dan katta fayl rad etiladi
- [ ] 400 pikseldan kichik rasm rad etiladi
- [ ] EXIF `orientation=6` bo'lgan rasmda kenglik va balandlik almashadi
- [ ] Saqlangan faylda EXIF yo'q
- [ ] Uzun tomoni 1600 dan katta rasm kichrayadi
- [ ] Rozilik belgisisiz rad etiladi, belgi bilan `consent_at` yoziladi
- [ ] Saqlangan fayl nomi yuklangan nomni o'z ichiga olmaydi

**Holatlar**

- [ ] `pending` va `approved`da yangi rasm yuklab bo'lmaydi
- [ ] `rejected`dan keyin yuklash mumkin va yangi yozuv yaratiladi
- [ ] Bazadagi cheklov ikkinchi `pending`ga yo'l qo'ymaydi
- [ ] `approve` va `reject` `reviewed_by`, `reviewed_at`ni to'ldiradi
- [ ] Sababsiz `reject` xato beradi
- [ ] `rejected`ni tasdiqlab bo'lmaydi, `approved`ni qayta tasdiqlab bo'lmaydi

**Ruxsatlar**

- [ ] Mehmon rasm manzilidan `/login/`ga yuboriladi
- [ ] Egasi va `is_staff` rasmni oladi
- [ ] Boshqa foydalanuvchi 404 oladi
- [ ] Javobda `Cache-Control: private, no-store` bor
- [ ] `/media/...` va `/private_media/...` manzillari 404 qaytaradi
- [ ] Oddiy foydalanuvchi admin tugmalari manzillariga kira olmaydi

**Fayllarni o'chirish**

- [ ] `reject`dan keyin fayl diskda yo'q
- [ ] `FaceTemplate` o'chirilsa, fayl diskda yo'q
- [ ] Foydalanuvchi o'chirilsa, uning fayllari diskda yo'q

Testga oid eslatmalar:

- Fayllar `tmp_path`ga yoziladi, `PRIVATE_MEDIA_ROOT` test vaqtida shunga almashtiriladi.
- `on_commit` test tranzaksiyasi ichida ishlamaydi, `django_capture_on_commit_callbacks(execute=True)` ishlating.

## 15. Qo'lda sinash ssenariysi

Kompyuterda bir marta, keyin telefonda bir marta bajariladi. Telefon uchun:
`python manage.py runserver 0.0.0.0:8000` va kompyuter IP manzili `DJANGO_ALLOWED_HOSTS`ga qo'shiladi.
Bu bosqichda kamera yo'q, shuning uchun oddiy HTTP yetarli.

1. Yangi foydalanuvchi ro'yxatdan o'tadi. Profilda «Rasm yuklanmagan» chiqadi.
2. Rozilik belgisisiz yuklashga urinadi, xato chiqadi.
3. Telefonda olingan rasmni yuklaydi. Profilda rasm to'g'ri tomonga qaragan va «Admin tekshirmoqda» yozilgan.
4. `/profile/photo/`ga qo'lda kiradi. Forma ochilmaydi, xabar bilan profilga qaytadi.
5. Boshqa brauzerda ikkinchi foydalanuvchi bilan birinchisining rasm manzilini ochadi, 404 chiqadi.
6. Admin rasmni rad etadi va sabab yozadi. Profilda sabab ko'rinadi, diskdagi fayl yo'qolgan.
7. Foydalanuvchi yangi rasm yuklaydi, admin tasdiqlaydi. Profilda «Tasdiqlangan», yuklash tugmasi yo'q.
8. Admin rasmni bekor qiladi va sabab yozadi. Foydalanuvchi yana yuklay oladi.
9. Admin foydalanuvchini o'chiradi. Uning papkasida fayl qolmagan.

## 16. Bosqich tugadi deyish uchun

- [ ] T1–T8 bajarilgan va `main`da
- [ ] `ruff check .` toza, `pytest` to'liq o'tadi
- [ ] Toza klon faqat README bo'yicha ishga tushadi
- [ ] 15-bo'limdagi ssenariy kompyuter va telefonda o'tdi
- [ ] `git ls-files`da `.env` va real rasm yo'q
- [ ] Ibrohimga demo ko'rsatildi

## 17. Ish tartibi

- `main`ga to'g'ridan-to'g'ri push qilinmaydi. Har vazifa alohida branch'da (`t3-register`), PR ochiladi va yana bir kishi ko'rib chiqadi.
- Bir ilovaning modellarini bir vaqtda faqat bitta odam o'zgartiradi, aks holda migratsiyalar to'qnashadi.
- `2-bosqichga tayyorlik` bahonasi bilan oldindan kod yozilmaydi. `embedding` va `model_name` maydonlaridan tashqari kelajak uchun hech narsa kerak emas.
