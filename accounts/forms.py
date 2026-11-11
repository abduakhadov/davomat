from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, label="Ism")
    last_name = forms.CharField(max_length=50, required=True, label="Familiya")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username")

    def clean_username(self):
        username = self.cleaned_data.get("username")
        return username.lower() if username else username


class LoginForm(AuthenticationForm):
    def clean_username(self):
        username = self.cleaned_data.get("username")
        return username.lower() if username else username
