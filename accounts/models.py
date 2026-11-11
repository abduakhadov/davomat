import re

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models


def validate_username(value):
    if not re.match(r"^[a-z0-9_]{3,30}$", value):
        raise ValidationError(
            "Username 3-30 belgidan iborat bo'lib, faqat kichik lotin harflari, raqam va '_' belgilaridan iborat bo'lishi kerak."
        )


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username kiritilishi shart.")
        username = username.lower()
        validate_username(username)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField(
        max_length=30, unique=True, validators=[validate_username]
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    EMAIL_FIELD = None
    email = None

    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def clean(self):
        super().clean()
        if self.username:
            self.username = self.username.lower()

    def save(self, *args, **kwargs):
        if self.username:
            self.username = self.username.lower()
        super().save(*args, **kwargs)
