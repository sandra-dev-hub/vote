from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Utilisateur


# -----------------------------
# ADMIN FORMS (CUSTOM)
# -----------------------------

class UserAdminChangeForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ("email", "matricule", "is_active", "is_staff", "is_superuser")


class UserAdminCreationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Utilisateur
        fields = ("email", "matricule")

    def clean_password2(self):
        if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
            raise forms.ValidationError("Passwords do not match")
        return self.cleaned_data["password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = ("email", "matricule")