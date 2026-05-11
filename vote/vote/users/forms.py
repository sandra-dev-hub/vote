from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import Utilisateur, Scrutin, DemandeElecteur, DemandeCandidature


# ======================
# ADMIN FORMS
# ======================
class UserAdminChangeForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ("email", "matricule", "nom", "prenom", "role", "is_staff", "is_active")


class UserAdminCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Utilisateur
        fields = ("email", "matricule")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# ======================
# USER FORMS
# ======================
class UserRegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = ("email", "matricule")


class ScrutinForm(forms.ModelForm):
    class Meta:
        model = Scrutin
        fields = ["titre", "description", "date_debut", "date_fin", "statut"]
        widgets = {
            "date_debut": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "date_fin": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class DemandeElecteurForm(forms.ModelForm):
    class Meta:
        model = DemandeElecteur
        fields = ["scrutin", "commentaire"]
        widgets = {
            "commentaire": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Commentaire optionnel..."
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commentaire"].required = False
        self.fields["scrutin"].queryset = Scrutin.objects.filter(statut="ouvert")


class DemandeCandidatureForm(forms.ModelForm):
    class Meta:
        model = DemandeCandidature
        fields = ["scrutin", "commentaire"]
        widgets = {
            "commentaire": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Lettre de motivation ou commentaire..."
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commentaire"].required = False
        self.fields["scrutin"].queryset = Scrutin.objects.filter(statut="ouvert")