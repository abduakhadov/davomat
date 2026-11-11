from django import forms


class PhotoUploadForm(forms.Form):
    image = forms.FileField(
        label="Rasm tanlang",
        widget=forms.ClearableFileInput(
            attrs={"accept": "image/jpeg,image/png", "class": "form-control"}
        ),
        error_messages={
            "required": "Iltimos, rasm faylini tanlang.",
        },
    )
    consent = forms.BooleanField(
        required=True,
        label="Yuz rasmim ishga kelib-ketishni belgilash uchun ishlatilishiga va tizimda saqlanishiga roziman.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        error_messages={
            "required": "Davom etish uchun rozilik belgisini qo'ying.",
        },
    )
