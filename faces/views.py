import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PhotoUploadForm
from .models import FaceTemplate
from .recognition import face_engine
from .services import get_current_template, submit_photo


@login_required
def photo_upload_view(request):
    current = get_current_template(request.user)

    # Agar rasm allaqachon tekshiruvda yoki tasdiqlangan bo'lsa, xabar bilan profilga qaytaramiz
    if current:
        if current.status == "pending":
            messages.warning(request, "Rasmingiz tekshirilmoqda, hozir yangisini yuklab bo'lmaydi.")
            return redirect("profile")
        elif current.status == "approved":
            messages.warning(request, "Rasmingiz tasdiqlangan. O'zgartirish uchun adminga murojaat qiling.")
            return redirect("profile")

    if request.method == "POST":
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                submit_photo(
                    user=request.user,
                    uploaded_file=form.cleaned_data["image"],
                )
                return redirect("profile")
            except ValidationError as e:
                form.add_error(None, e.message if hasattr(e, "message") else str(e))
    else:
        form = PhotoUploadForm()

    return render(request, "faces/photo_upload.html", {"form": form})


@login_required
def secure_image_view(request, pk):
    template = get_object_or_404(FaceTemplate, pk=pk)

    # Faqat egasi yoki admin (is_staff) ko'ra oladi, boshqalar 404 oladi
    if not request.user.is_staff and template.user != request.user:
        raise Http404("Rasm topilmadi.")

    if not template.image:
        raise Http404("Rasm mavjud emas.")

    try:
        with template.image.open("rb") as f:
            file_data = f.read()

        response = HttpResponse(file_data, content_type="image/jpeg")
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
    except Exception:
        raise Http404("Fayl topilmadi.")


def davomat_view(request):
    """
    Davomat sahifasi:
    Brauzer orqali kamerani yoqib, rasmlar papkasidagi baza bilan yuzni solishtirish.
    """
    face_engine.ensure_database_loaded()
    ismlar = face_engine.ismlar
    return render(
        request,
        "faces/davomat.html",
        {
            "ismlar": ismlar,
            "odamlar_soni": len(ismlar),
        },
    )


@require_POST
def davomat_check_api(request):
    """
    Kameradan olingan kadrni (base64) qabul qilib, bazadagi odamlar bilan solishtiradi.
    """
    try:
        if request.content_type == "application/json":
            data = json.loads(request.body.decode("utf-8"))
            image_data = data.get("image", "")
        else:
            image_data = request.POST.get("image", "")

        if not image_data:
            return JsonResponse({"success": False, "message": "Rasm yuborilmadi"}, status=400)

        result = face_engine.process_base64_image(image_data)
        result["success"] = True
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Xatolik yuz berdi: {e}"}, status=500)


@require_POST
def davomat_reload_db_api(request):
    """
    'rasmlar' papkasidagi yangilangan fayllarni qayta yuklash API.
    """
    try:
        ismlar = face_engine.reload_database()
        return JsonResponse({
            "success": True,
            "odamlar_soni": len(ismlar),
            "ismlar": ismlar,
            "message": f"Baza yangilandi! Jami {len(ismlar)} kishi yuklandi.",
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Xatolik: {e}"}, status=500)

