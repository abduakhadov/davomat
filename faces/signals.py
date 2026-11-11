from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import FaceTemplate


@receiver(post_delete, sender=FaceTemplate)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """FaceTemplate o'chganda (yoki user o'chganda CASCADE orqali) faylni diskdan tozalash"""
    if instance.image:
        image_name = instance.image.name
        storage = instance.image.storage
        transaction.on_commit(lambda: storage.delete(image_name))
