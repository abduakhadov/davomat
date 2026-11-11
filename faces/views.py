from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PhotoUploadForm
from .models import FaceTemplate
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
