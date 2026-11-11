from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from .images import process_face_image
from .models import FaceTemplate

User = get_user_model()


def get_current_template(user):
    """Foydalanuvchining created_at bo'yicha eng oxirgi FaceTemplate yozuvi"""
    return user.face_templates.order_by("-created_at").first()


@transaction.atomic
def submit_photo(user, uploaded_file) -> FaceTemplate:
    """
    Yangi rasm yuklash (bitta tranzaksiyada):
    1. Foydalanuvchi qatorini select_for_update bilan qulflaydi.
    2. Yuklash mumkinligini tekshiradi (faqat rasm yo'q yoki oxirgisi rejected bo'lsa).
    3. FaceTemplate yaratadi, consent_at ga hozirgi vaqtni yozadi.
    """
    locked_user = User.objects.select_for_update().get(pk=user.pk)
    current = get_current_template(locked_user)

    if current:
        if current.status == "pending":
            raise ValidationError("Rasmingiz tekshirilmoqda, hozir yangisini yuklab bo'lmaydi.")
        elif current.status == "approved":
            raise ValidationError("Rasmingiz tasdiqlangan. O'zgartirish uchun adminga murojaat qiling.")

    # 9-bo'lim bo'yicha rasmni tekshirish va tozalash
    image_content, file_path = process_face_image(uploaded_file, locked_user.pk)

    try:
        template = FaceTemplate(
            user=locked_user,
            status="pending",
            consent_at=timezone.now(),
        )
        template.image.save(file_path, image_content, save=False)
        template.save()
        return template
    except IntegrityError:
        raise ValidationError("Sizda allaqachon faol (pending yoki approved) rasm mavjud.")


@transaction.atomic
def approve(template, reviewer) -> FaceTemplate:
    """
    Pending holatidagi rasmni tasdiqlash.
    Ruxsat etilgan o'tish: pending -> approved.
    reviewed_by va reviewed_at ni to'ldiradi.
    """
    locked_template = FaceTemplate.objects.select_for_update().get(pk=template.pk)

    if locked_template.status != "pending":
        raise ValidationError("Faqat 'pending' holatidagi rasmni tasdiqlash mumkin.")

    locked_template.status = "approved"
    locked_template.reviewed_by = reviewer
    locked_template.reviewed_at = timezone.now()
    locked_template.save()
    return locked_template


@transaction.atomic
def reject(template, reviewer, reason: str) -> FaceTemplate:
    """
    Pending yoki Approved holatidagi rasmni rad etish / bekor qilish.
    Ruxsat etilgan o'tishlar: pending -> rejected, approved -> rejected.
    Sabab bo'sh bo'lsa xato; reviewed_by, reviewed_at ni to'ldiradi, rasm faylini o'chiradi.
    """
    locked_template = FaceTemplate.objects.select_for_update().get(pk=template.pk)

    if locked_template.status not in ["pending", "approved"]:
        raise ValidationError("Faqat 'pending' yoki 'approved' holatidagi rasmni rad etish mumkin.")

    if not reason or not reason.strip():
        raise ValidationError("Rad etish sababi ko'rsatilishi shart.")

    locked_template.status = "rejected"
    locked_template.rejection_reason = reason.strip()
    locked_template.reviewed_by = reviewer
    locked_template.reviewed_at = timezone.now()

    # Rasm faylini xavfsiz o'chirish (tranzaksiya tugagach) va maydonni bo'shatish
    image_to_delete = locked_template.image
    locked_template.image = ""
    locked_template.save()

    if image_to_delete and image_to_delete.name:
        storage = image_to_delete.storage
        name = image_to_delete.name
        transaction.on_commit(lambda: storage.delete(name))

    return locked_template
