"""Forms for the users app."""

import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import User


class LoginForm(AuthenticationForm):
    """Styled login form using Bootstrap 5 classes."""

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
            }
        ),
    )


class ProfileForm(forms.ModelForm):
    """Form for users to update their profile (name and WhatsApp number)."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nama depan",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nama belakang",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contoh: 6281234567890",
                }
            ),
        }
        labels = {
            "first_name": "Nama Depan",
            "last_name": "Nama Belakang",
            "phone": "Nomor WhatsApp",
        }
        help_texts = {
            "phone": "Wajib diisi. Format: 62xxxxxxxxxx (tanpa + atau spasi).",
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            raise forms.ValidationError(
                "Nomor WhatsApp wajib diisi agar dapat menerima notifikasi."
            )
        # Remove common formatting characters
        phone = re.sub(r"[\s\-\+\(\)]", "", phone)
        # Convert leading 0 to 62
        if phone.startswith("0"):
            phone = "62" + phone[1:]
        if not phone.startswith("62"):
            raise forms.ValidationError(
                "Nomor harus diawali dengan 62 (kode negara Indonesia)."
            )
        if not phone.isdigit():
            raise forms.ValidationError("Nomor hanya boleh berisi angka.")
        if len(phone) < 10 or len(phone) > 15:
            raise forms.ValidationError("Panjang nomor tidak valid (10-15 digit).")
        return phone


class UserCreateForm(forms.ModelForm):
    """Form for GA/Manager to create a new user account."""

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Minimal 8 karakter",
            }
        ),
        label="Password",
        min_length=8,
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ulangi password",
            }
        ),
        label="Konfirmasi Password",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "role", "phone"]
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Username login",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nama depan",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nama belakang",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "email@example.com",
                }
            ),
            "role": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "6281234567890",
                }
            ),
        }
        labels = {
            "username": "Username",
            "first_name": "Nama Depan",
            "last_name": "Nama Belakang",
            "email": "Email",
            "role": "Role",
            "phone": "Nomor WhatsApp",
        }

    def clean_password_confirm(self):
        pw = self.cleaned_data.get("password")
        pw2 = self.cleaned_data.get("password_confirm")
        if pw and pw2 and pw != pw2:
            raise forms.ValidationError("Password tidak cocok.")
        return pw2

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if phone:
            phone = re.sub(r"[\s\-\+\(\)]", "", phone)
            if phone.startswith("0"):
                phone = "62" + phone[1:]
            if not phone.startswith("62"):
                raise forms.ValidationError("Nomor harus diawali dengan 62.")
            if not phone.isdigit():
                raise forms.ValidationError("Nomor hanya boleh berisi angka.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class AdminSetPasswordForm(forms.Form):
    """Form for GA/Manager to reset a user's password (no old password needed)."""

    new_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password baru (min. 8 karakter)",
            }
        ),
        label="Password Baru",
        min_length=8,
    )
    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ulangi password baru",
            }
        ),
        label="Konfirmasi Password Baru",
    )

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("new_password")
        pw2 = cleaned.get("new_password_confirm")
        if pw and pw2 and pw != pw2:
            raise forms.ValidationError("Password tidak cocok.")
        return cleaned


class ChangePasswordForm(forms.Form):
    """Form for users to change their own password (requires old password)."""

    old_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password saat ini",
            }
        ),
        label="Password Lama",
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password baru (min. 8 karakter)",
            }
        ),
        label="Password Baru",
        min_length=8,
    )
    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ulangi password baru",
            }
        ),
        label="Konfirmasi Password Baru",
    )

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("new_password")
        pw2 = cleaned.get("new_password_confirm")
        if pw and pw2 and pw != pw2:
            raise forms.ValidationError("Password baru tidak cocok.")
        return cleaned
