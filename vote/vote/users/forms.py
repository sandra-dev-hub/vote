from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur, Scrutin, DemandeElecteur, DemandeCandidature


# ======================
# ADMIN FORMS
# ======================
class UserAdminChangeForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ("email", "matricule", "nom", "prenom", "role", "is_staff", "is_active")


class UserAdminCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="Confirmation du mot de passe", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

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
    filiere = forms.CharField(
        label="Filière", required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-5 py-4 bg-gray-50 border border-transparent rounded-2xl focus:bg-white focus:ring-2 focus:ring-brand-500/20 focus:border-brand-100 focus:outline-none transition-all text-sm font-semibold',
            'placeholder': 'Ex: Génie Logiciel, Management...'
        })
    )
    niveau = forms.CharField(
        label="Niveau", required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-5 py-4 bg-gray-50 border border-transparent rounded-2xl focus:bg-white focus:ring-2 focus:ring-brand-500/20 focus:border-brand-100 focus:outline-none transition-all text-sm font-semibold',
            'placeholder': 'Ex: L3, Master 1...'
        })
    )
    photo = forms.ImageField(
        label="Photo de profil",
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*',
            'id': 'id_photo'
        })
    )

    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = ("email", "matricule", "nom", "prenom", "filiere", "niveau", "photo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['email', 'matricule', 'nom', 'prenom', 'password1', 'password2']:
            self.fields[field].widget.attrs.update({
                'class': 'w-full px-5 py-4 bg-gray-50 border border-transparent rounded-2xl focus:bg-white focus:ring-2 focus:ring-brand-500/20 focus:border-brand-100 focus:outline-none transition-all text-sm font-semibold'
            })


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
        widgets = {"commentaire": forms.Textarea(attrs={"rows": 3, "placeholder": "Commentaire optionnel..."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commentaire"].required = False
        self.fields["scrutin"].queryset = Scrutin.objects.filter(statut="ouvert")


class DemandeCandidatureForm(forms.ModelForm):
    class Meta:
        model = DemandeCandidature
        fields = ["scrutin", "commentaire"]
        widgets = {"commentaire": forms.Textarea(attrs={"rows": 4, "placeholder": "Lettre de motivation..."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commentaire"].required = False
        self.fields["scrutin"].queryset = Scrutin.objects.filter(statut="ouvert")