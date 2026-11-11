import io
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError
from PIL.Image import DecompressionBombError


def process_face_image(uploaded_file, user_id):
    """
    Rasmni qabul qilish va tozalash (task.md 9-bo'lim):
    1. Hajm tekshiruvi (FACE_MAX_UPLOAD_BYTES)
    2. Image.open(formats=['JPEG', 'PNG'])
    3. FACE_MAX_PIXELS tekshiruvi (dekompressiya bombasi)
    4. To'liq yuklash (img.load), xatolar forma xatosiga aylanadi
    5. ImageOps.exif_transpose
    6. Kichik tomoni FACE_MIN_SIDE dan kam bo'lsa rad etiladi
    7. RGB ga o'tkaziladi, shaffof fon oq bilan to'ldiriladi
    8. Uzun tomoni FACE_MAX_SIDE dan katta bo'lsa kichraytiriladi
    9. JPEG (quality 90, EXIF'siz) sifatida tayyorlanadi
    10. Fayl yo'li: faces/<user_id>/<uuid4>.jpg
    """
    max_bytes = getattr(settings, "FACE_MAX_UPLOAD_BYTES", 10 * 1024 * 1024)
    min_side = getattr(settings, "FACE_MIN_SIDE", 400)
    max_side = getattr(settings, "FACE_MAX_SIDE", 1600)
    max_pixels = getattr(settings, "FACE_MAX_PIXELS", 50_000_000)

    # 1. Fayl hajmi tekshiruvi
    if uploaded_file.size > max_bytes:
        raise ValidationError("Rasm hajmi 10 MB dan oshmasin.")

    # 2 & 3 & 4. Image.open, dekompressiya bombasi va to'liq o'qish
    Image.MAX_IMAGE_PIXELS = max_pixels
    uploaded_file.seek(0)
    try:
        img = Image.open(uploaded_file, formats=["JPEG", "PNG"])

        # 3. Kenglik × balandlik FACE_MAX_PIXELS dan katta bo'lsa
        width, height = img.size
        if width * height > max_pixels:
            raise ValidationError("Rasm juda katta o'lchamda. Boshqa rasm tanlang.")

        # 4. Rasm to'liq o'qiladi
        img.load()
    except (UnidentifiedImageError, ValueError):
        raise ValidationError("Faqat JPEG yoki PNG rasm yuklang.")
    except DecompressionBombError:
        raise ValidationError("Rasm juda katta o'lchamda. Boshqa rasm tanlang.")
    except (OSError, Exception):
        raise ValidationError("Rasmni o'qib bo'lmadi. Boshqa fayl tanlang.")

    # 5. ImageOps.exif_transpose
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    width, height = img.size

    # 6. Kichik tomoni FACE_MIN_SIDE dan kam bo'lsa
    if min(width, height) < min_side:
        raise ValidationError("Rasm juda kichik: kamida 400×400 piksel bo'lsin.")

    # 7. RGB ga o'tkaziladi, shaffof fon oq bilan to'ldiriladi
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # 8. Uzun tomoni FACE_MAX_SIDE dan katta bo'lsa kichraytiriladi
    if max(width, height) > max_side:
        img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    # 9. JPEG (quality 90) sifatida, EXIF'siz saqlanadi
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    # 10. Fayl yo'li: faces/<user_id>/<uuid4>.jpg
    file_path = f"faces/{user_id}/{uuid.uuid4()}.jpg"
    return ContentFile(buffer.read()), file_path
