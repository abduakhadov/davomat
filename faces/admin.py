from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import FaceTemplate
from .services import approve, reject


@admin.register(FaceTemplate)
class FaceTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail_tag",
        "user_full_name",
        "status",
        "created_at",
        "reviewed_by",
        "reviewed_at",
    )
    list_filter = ("status",)
    search_fields = ("user__username", "user__first_name", "user__last_name")
    ordering = ("-created_at",)
    actions = ["approve_selected"]

    readonly_fields = (
        "id",
        "user",
        "status",
        "preview_image_tag",
        "consent_at",
        "rejection_reason",
        "reviewed_by",
        "reviewed_at",
        "embedding",
        "model_name",
        "created_at",
    )
    fields = (
        "preview_image_tag",
        "user",
        "status",
        "consent_at",
        "rejection_reason",
        "reviewed_by",
        "reviewed_at",
        "model_name",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="Kichik rasm")
    def thumbnail_tag(self, obj):
        if obj.image:
            url = reverse("secure_image", kwargs={"pk": obj.pk})
            return format_html('<img src="{}" style="height: 45px; border-radius: 4px;" />', url)
        return "—"

    @admin.display(description="Ism-familiya")
    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    @admin.display(description="Rasm")
    def preview_image_tag(self, obj):
        if obj.image:
            url = reverse("secure_image", kwargs={"pk": obj.pk})
            return format_html('<img src="{}" style="max-height: 350px; border-radius: 6px;" />', url)
        return "— (Rasm mavjud emas)"

    @admin.action(description="Tanlanganlarni tasdiqlash")
    def approve_selected(self, request, queryset):
        approved_count = 0
        skipped_count = 0
        for template in queryset:
            if template.status == "pending":
                try:
                    approve(template, request.user)
                    approved_count += 1
                except Exception:
                    skipped_count += 1
            else:
                skipped_count += 1

        if approved_count:
            self.message_user(
                request,
                f"{approved_count} ta rasm tasdiqlandi.",
                level=messages.SUCCESS,
            )
        if skipped_count:
            self.message_user(
                request,
                f"{skipped_count} ta rasm holati 'pending' bo'lmagani sababli o'tkazib yuborildi.",
                level=messages.WARNING,
            )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<uuid:pk>/admin-approve/",
                self.admin_site.admin_view(self.admin_approve_view),
                name="faces_facetemplate_approve",
            ),
            path(
                "<uuid:pk>/admin-reject/",
                self.admin_site.admin_view(self.admin_reject_view),
                name="faces_facetemplate_reject",
            ),
        ]
        return custom_urls + urls

    def admin_approve_view(self, request, pk):
        if request.method == "POST":
            template = self.get_object(request, pk)
            if not template:
                self.message_user(request, "Rasm yozuvi topilmadi.", level=messages.ERROR)
            elif not self.has_change_permission(request, template):
                self.message_user(request, "Ruxsat berilmagan.", level=messages.ERROR)
            else:
                try:
                    approve(template, request.user)
                    self.message_user(request, "Rasm muvaffaqiyatli tasdiqlandi.", level=messages.SUCCESS)
                except Exception as e:
                    self.message_user(request, f"Xatolik: {e}", level=messages.ERROR)
        return HttpResponseRedirect(reverse("admin:faces_facetemplate_change", args=[pk]))

    def admin_reject_view(self, request, pk):
        if request.method == "POST":
            template = self.get_object(request, pk)
            if not template:
                self.message_user(request, "Rasm yozuvi topilmadi.", level=messages.ERROR)
            elif not self.has_change_permission(request, template):
                self.message_user(request, "Ruxsat berilmagan.", level=messages.ERROR)
            else:
                reason = request.POST.get("rejection_reason", "").strip()
                if not reason:
                    self.message_user(request, "Rad etish / bekor qilish sababini kiritish shart!", level=messages.ERROR)
                else:
                    try:
                        reject(template, request.user, reason)
                        self.message_user(request, "Rasm muvaffaqiyatli rad etildi / bekor qilindi.", level=messages.SUCCESS)
                    except Exception as e:
                        self.message_user(request, f"Xatolik: {e}", level=messages.ERROR)
        return HttpResponseRedirect(reverse("admin:faces_facetemplate_change", args=[pk]))

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        template = self.get_object(request, object_id)
        extra_context["template_obj"] = template
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
