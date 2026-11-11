import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from .storage import get_private_storage


def face_upload_path(instance, filename):
    return f"faces/{instance.user_id}/{uuid.uuid4()}.jpg"


class FaceTemplate(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="face_templates",
    )
    image = models.ImageField(
        storage=get_private_storage,
        upload_to=face_upload_path,
        blank=True,
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    consent_at = models.DateTimeField()
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    embedding = models.BinaryField(null=True, blank=True)
    model_name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status__in=["pending", "approved"]),
                name="one_live_face_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.status}"
