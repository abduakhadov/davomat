import io
import shutil
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import User
from faces.models import FaceTemplate
from faces.services import approve, get_current_template, reject, submit_photo


def create_test_image(size=(500, 500), format="JPEG", mode="RGB", color=(200, 100, 50), orientation=None):
    """Pillow bilan test uchun rasm generatsiya qiluvchi yordamchi funksiya"""
    img = Image.new(mode, size, color)
    buffer = io.BytesIO()
    
    if orientation:
        exif = img.getexif()
        exif[0x0112] = orientation  # Orientation tag
        img.save(buffer, format=format, exif=exif)
    else:
        img.save(buffer, format=format)
        
    buffer.seek(0)
    ext = "png" if format.upper() == "PNG" else "jpg"
    return SimpleUploadedFile(f"test_photo.{ext}", buffer.read(), content_type=f"image/{ext}")


class FaceSystemTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.mkdtemp()
        self.settings_override = override_settings(PRIVATE_MEDIA_ROOT=self.temp_media)
        self.settings_override.enable()

        self.user = User.objects.create_user(
            username="testuser",
            password="StrongPassword123!",
            first_name="Anvar",
            last_name="Karimov",
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            password="StrongPassword123!",
            first_name="Jasur",
            last_name="Aliyev",
        )
        self.admin_user = User.objects.create_superuser(
            username="adminuser",
            password="StrongPassword123!",
            first_name="Admin",
            last_name="Super",
        )

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.temp_media, ignore_errors=True)

    # --- 1. Rasm yuklash testlari ---
    def test_jpeg_accepted(self):
        photo = create_test_image(size=(600, 600), format="JPEG")
        template = submit_photo(self.user, photo)
        self.assertEqual(template.status, "pending")
        self.assertTrue(template.image)
        self.assertTrue(template.image.name.endswith(".jpg"))

    def test_transparent_png_converted_to_jpeg(self):
        photo = create_test_image(size=(600, 600), format="PNG", mode="RGBA", color=(100, 100, 100, 128))
        template = submit_photo(self.user, photo)
        self.assertEqual(template.status, "pending")
        # Rasm JPEG ekanligini tekshiramiz
        with template.image.open("rb") as f:
            opened = Image.open(f)
            self.assertEqual(opened.format, "JPEG")
            self.assertEqual(opened.mode, "RGB")

    def test_gif_rejected(self):
        img = Image.new("RGB", (500, 500), "red")
        buffer = io.BytesIO()
        img.save(buffer, format="GIF")
        buffer.seek(0)
        photo = SimpleUploadedFile("fake.gif", buffer.read(), content_type="image/gif")
        with self.assertRaises(ValidationError):
            submit_photo(self.user, photo)

    def test_fake_jpg_text_file_rejected_no_500(self):
        fake_file = SimpleUploadedFile("malicious.jpg", b"Bu matn fayl rasm emas", content_type="image/jpeg")
        with self.assertRaises(ValidationError):
            submit_photo(self.user, fake_file)

    def test_small_image_rejected(self):
        # 400 dan kichik
        small_photo = create_test_image(size=(350, 500))
        with self.assertRaises(ValidationError):
            submit_photo(self.user, small_photo)

    def test_large_side_resized(self):
        # 1600 dan katta tomon kichrayishi kerak
        large_photo = create_test_image(size=(2000, 1000))
        template = submit_photo(self.user, large_photo)
        with template.image.open("rb") as f:
            opened = Image.open(f)
            self.assertLessEqual(max(opened.size), 1600)

    def test_truncated_jpeg_rejected_no_500(self):
        # Yarmi kesilgan JPEG rad etiladi, 500 chiqmaydi
        photo = create_test_image(size=(500, 500), format="JPEG")
        raw_bytes = photo.read()
        truncated_content = raw_bytes[: len(raw_bytes) // 2]
        truncated_file = SimpleUploadedFile("truncated.jpg", truncated_content, content_type="image/jpeg")
        with self.assertRaises(ValidationError):
            submit_photo(self.user, truncated_file)

    def test_file_larger_than_10mb_rejected(self):
        # 10 MB dan katta fayl rad etiladi
        large_bytes = b"0" * (10 * 1024 * 1024 + 1024)
        large_file = SimpleUploadedFile("big.jpg", large_bytes, content_type="image/jpeg")
        with self.assertRaises(ValidationError):
            submit_photo(self.user, large_file)

    def test_exif_orientation_6_swaps_width_height(self):
        # EXIF orientation=6 bo'lgan rasmda kenglik va balandlik almashadi (600x400 -> 400x600)
        photo = create_test_image(size=(600, 400), orientation=6)
        template = submit_photo(self.user, photo)
        with template.image.open("rb") as f:
            opened = Image.open(f)
            self.assertEqual(opened.size, (400, 600))

    def test_saved_image_has_no_exif_and_random_name(self):
        photo = create_test_image(size=(500, 500), orientation=6)
        template = submit_photo(self.user, photo)
        
        # Asl fayl nomi ("test_photo.jpg") yo'qligini tekshiramiz
        self.assertNotIn("test_photo", template.image.name)
        
        # EXIF o'chirilganligini tekshiramiz
        with template.image.open("rb") as f:
            opened = Image.open(f)
            exif = opened.getexif()
            self.assertEqual(len(exif), 0)

    # --- 2. Holatlar testlari ---
    def test_cannot_upload_when_pending_or_approved(self):
        photo1 = create_test_image(size=(500, 500))
        submit_photo(self.user, photo1)

        # Pending holatda ikkinchi rasm yuklab bo'lmaydi
        photo2 = create_test_image(size=(500, 500))
        with self.assertRaises(ValidationError):
            submit_photo(self.user, photo2)

        # Approved qilingandan keyin ham yuklab bo'lmaydi
        template = get_current_template(self.user)
        approve(template, self.admin_user)

        photo3 = create_test_image(size=(500, 500))
        with self.assertRaises(ValidationError):
            submit_photo(self.user, photo3)

    def test_db_unique_constraint_blocks_second_active_template(self):
        # Bazadagi cheklov (UniqueConstraint) ikkinchi pending/approved ga yo'l qo'ymaydi
        FaceTemplate.objects.create(user=self.user, status="pending", consent_at=timezone.now())
        with self.assertRaises(IntegrityError):
            FaceTemplate.objects.create(user=self.user, status="pending", consent_at=timezone.now())

    def test_upload_allowed_after_reject(self):
        photo1 = create_test_image(size=(500, 500))
        template1 = submit_photo(self.user, photo1)
        reject(template1, self.admin_user, "Rasm qorong'i tushgan")

        # Rejected dan keyin yangi rasm yuklash mumkin
        photo2 = create_test_image(size=(500, 500))
        template2 = submit_photo(self.user, photo2)
        self.assertEqual(template2.status, "pending")
        self.assertNotEqual(template1.pk, template2.pk)

    def test_reject_without_reason_fails(self):
        photo = create_test_image(size=(500, 500))
        template = submit_photo(self.user, photo)
        with self.assertRaises(ValidationError):
            reject(template, self.admin_user, "   ")

    def test_cannot_approve_rejected_or_reapprove(self):
        photo = create_test_image(size=(500, 500))
        template = submit_photo(self.user, photo)
        reject(template, self.admin_user, "Rad etildi")

        # Rad etilganni tasdiqlab bo'lmaydi
        with self.assertRaises(ValidationError):
            approve(template, self.admin_user)

    def test_upload_without_consent_fails_and_with_consent_sets_consent_at(self):
        # Rozilik belgisisiz rad etiladi, belgi bilan consent_at yoziladi
        self.client.force_login(self.user)
        upload_url = reverse("photo_upload")
        photo = create_test_image(size=(500, 500))

        # 1. Rozilik belgisisiz (consent=False)
        resp = self.client.post(upload_url, {"image": photo, "consent": False})
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp.context["form"], "consent", "Davom etish uchun rozilik belgisini qo'ying.")
        self.assertIsNone(get_current_template(self.user))

        # 2. Rozilik belgisi bilan (consent=True)
        photo.seek(0)
        resp = self.client.post(upload_url, {"image": photo, "consent": True})
        self.assertEqual(resp.status_code, 302)
        template = get_current_template(self.user)
        self.assertIsNotNone(template)
        self.assertIsNotNone(template.consent_at)

    def test_photo_upload_view_redirects_with_warning_when_has_active(self):
        # Pending yoki approved rasm bo'lsa, /profile/photo/ dan xabar bilan /profile/ ga qaytadi
        photo = create_test_image(size=(500, 500))
        submit_photo(self.user, photo)

        self.client.force_login(self.user)
        upload_url = reverse("photo_upload")
        resp = self.client.get(upload_url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("profile"))

    # --- 3. Ruxsatlar testlari ---
    def test_guest_redirected_to_login(self):
        photo = create_test_image(size=(500, 500))
        template = submit_photo(self.user, photo)
        url = reverse("secure_image", kwargs={"pk": template.pk})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_owner_and_staff_can_view_image(self):
        photo = create_test_image(size=(500, 500))
        template = submit_photo(self.user, photo)
        url = reverse("secure_image", kwargs={"pk": template.pk})

        # Egasi ko'ra oladi
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

        # Admin (is_staff) ko'ra oladi
        self.client.force_login(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_other_user_gets_404(self):
        photo = create_test_image(size=(500, 500))
        template = submit_photo(self.user, photo)
        url = reverse("secure_image", kwargs={"pk": template.pk})

        # Boshqa foydalanuvchi 404 oladi (403 emas!)
        self.client.force_login(self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_media_and_private_media_return_404(self):
        # /media/... va /private_media/... manzillari 404 qaytaradi
        resp1 = self.client.get("/media/faces/sample.jpg")
        self.assertEqual(resp1.status_code, 404)
        resp2 = self.client.get("/private_media/faces/sample.jpg")
        self.assertEqual(resp2.status_code, 404)

    def test_regular_user_cannot_access_admin_action_urls(self):
        # Oddiy foydalanuvchi admin tugmalari manzillariga kira olmaydi
        photo = create_test_image(size=(500, 500))
        template = submit_photo(self.user, photo)
        approve_url = reverse("admin:faces_facetemplate_approve", kwargs={"pk": template.pk})

        self.client.force_login(self.user)
        resp = self.client.post(approve_url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login/", resp.url)

    def test_admin_approve_view_works(self):
        # Admin "Tasdiqlash" tugmasi ishlashini tekshirish
        photo = create_test_image(size=(500, 500))
        template = submit_photo(self.user, photo)
        self.assertEqual(template.status, "pending")

        self.client.force_login(self.admin_user)
        approve_url = reverse("admin:faces_facetemplate_approve", kwargs={"pk": template.pk})
        resp = self.client.post(approve_url)
        self.assertEqual(resp.status_code, 302)

        template.refresh_from_db()
        self.assertEqual(template.status, "approved")
        self.assertEqual(template.reviewed_by, self.admin_user)
        self.assertIsNotNone(template.reviewed_at)

    def test_admin_reject_view_works(self):
        # Admin "Rad etish" tugmasi ishlashini tekshirish
        photo = create_test_image(size=(500, 500))
        template = submit_photo(self.user, photo)
        self.assertEqual(template.status, "pending")

        self.client.force_login(self.admin_user)
        reject_url = reverse("admin:faces_facetemplate_reject", kwargs={"pk": template.pk})
        resp = self.client.post(reject_url, {"rejection_reason": "Yuz ko'rinmayapti"})
        self.assertEqual(resp.status_code, 302)

        template.refresh_from_db()
        self.assertEqual(template.status, "rejected")
        self.assertEqual(template.rejection_reason, "Yuz ko'rinmayapti")

    def test_admin_cancel_approved_view_works(self):
        # Admin "Bekor qilish" tugmasi (approved -> rejected) ishlashini tekshirish
        photo = create_test_image(size=(500, 500))
        template = submit_photo(self.user, photo)
        approve(template, self.admin_user)

        self.client.force_login(self.admin_user)
        reject_url = reverse("admin:faces_facetemplate_reject", kwargs={"pk": template.pk})
        resp = self.client.post(reject_url, {"rejection_reason": "Xodim rasmni yangilamoqchi"})
        self.assertEqual(resp.status_code, 302)

        template.refresh_from_db()
        self.assertEqual(template.status, "rejected")

    def test_admin_reject_without_reason_fails(self):
        # Sababsiz rad etishda xato chiqishi kerak
        photo = create_test_image(size=(500, 500))
        template = submit_photo(self.user, photo)

        self.client.force_login(self.admin_user)
        reject_url = reverse("admin:faces_facetemplate_reject", kwargs={"pk": template.pk})
        resp = self.client.post(reject_url, {"rejection_reason": ""})
        self.assertEqual(resp.status_code, 302)

        # Status o'zgarmasligi kerak
        template.refresh_from_db()
        self.assertEqual(template.status, "pending")

    # --- 4. Faylni o'chirish testlari ---
    def test_file_deleted_on_reject(self):
        photo = create_test_image(size=(500, 500))
        with self.captureOnCommitCallbacks(execute=True):
            template = submit_photo(self.user, photo)
            storage = template.image.storage
            file_name = template.image.name
            self.assertTrue(storage.exists(file_name))

            reject(template, self.admin_user, "Noto'g'ri rasm")

        # Reject bo'lgandan keyin fayl diskdan o'chgan bo'lishi kerak
        self.assertFalse(storage.exists(file_name))

    def test_file_deleted_on_template_delete(self):
        photo = create_test_image(size=(500, 500))
        with self.captureOnCommitCallbacks(execute=True):
            template = submit_photo(self.user, photo)
            storage = template.image.storage
            file_name = template.image.name
            self.assertTrue(storage.exists(file_name))

            template.delete()

        self.assertFalse(storage.exists(file_name))

    def test_file_deleted_on_user_delete(self):
        photo = create_test_image(size=(500, 500))
        with self.captureOnCommitCallbacks(execute=True):
            template = submit_photo(self.user, photo)
            storage = template.image.storage
            file_name = template.image.name
            self.assertTrue(storage.exists(file_name))

            self.user.delete()

        self.assertFalse(storage.exists(file_name))

