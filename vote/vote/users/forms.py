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
    FILIERES = [
        ("", "Sélectionner une filière"),
        ("GL", "Génie Logiciel"),
        ("RSI", "Réseaux et Sécurité Informatique"),
        ("MIAGE", "MIAGE"),
        ("MARKETING", "Marketing Digital"),
        ("COMPTA", "Comptabilité"),
    ]

    NIVEAUX = [
        ("", "Sélectionner un niveau"),
        ("N1", "Niveau 1"),
        ("N2", "Niveau 2"),
        ("N3", "Niveau 3"),
        ("M1", "Master 1"),
        ("M2", "Master 2"),
    ]

    filiere = forms.ChoiceField(
        choices=FILIERES,
        required=True
    )

    niveau = forms.ChoiceField(
        choices=NIVEAUX,
        required=True
    )

    photo = forms.ImageField(
        required=True,
        widget=forms.FileInput(
            attrs={
                "class": "hidden",
                "accept": "image/*",
                "id": "id_photo",
            }
        ),
    )

    class Meta:
        model = Utilisateur
        fields = (
            "email",
            "matricule",
            "nom",
            "prenom",
            "filiere",
            "niveau",
            "photo",
        )

    def clean_matricule(self):
        matricule = self.cleaned_data.get("matricule")

        if not matricule:
            raise forms.ValidationError(
                "Le matricule est obligatoire."
            )

        if not matricule.isdigit():
            raise forms.ValidationError(
                "Le matricule doit contenir uniquement des chiffres."
            )

        if len(matricule) != 6:
            raise forms.ValidationError(
                "Le matricule doit contenir exactement 6 chiffres."
            )

        matricule_complet = f"ICAB-2026-{matricule}"

        if Utilisateur.objects.filter(
            matricule=matricule_complet
        ).exists():
            raise forms.ValidationError(
                "Ce matricule existe déjà."
            )

        return matricule_complet

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")

        if photo:
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    "La photo ne doit pas dépasser 5 Mo."
                )

            allowed_types = [
                "image/jpeg",
                "image/png",
                "image/webp",
            ]

            if photo.content_type not in allowed_types:
                raise forms.ValidationError(
                    "Format invalide. JPG, PNG ou WEBP uniquement."
                )

        return photo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in [
            "email",
            "matricule",
            "nom",
            "prenom",
            "password1",
            "password2",
        ]:
            self.fields[field].widget.attrs.update({
                "class": "field-input"
            })


class ScrutinForm(forms.ModelForm):
    class Meta:
        model = Scrutin
        fields = [
            "titre", "description",
            "date_debut", "date_fin",          # Période 1 : candidatures
            "date_debut_vote", "date_fin_vote", # Période 2 : vote
            "statut",
        ]
        widgets = {
            "date_debut": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "date_fin": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "date_debut_vote": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "date_fin_vote": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get("date_debut")
        date_fin = cleaned_data.get("date_fin")
        date_debut_vote = cleaned_data.get("date_debut_vote")
        date_fin_vote = cleaned_data.get("date_fin_vote")

        if date_debut and date_fin and date_debut >= date_fin:
            self.add_error("date_fin", "La fin de la période 1 doit être après son début.")

        if date_debut_vote and date_fin_vote and date_debut_vote >= date_fin_vote:
            self.add_error("date_fin_vote", "La fin du vote doit être après son début.")

        if date_fin and date_debut_vote and date_debut_vote <= date_fin:
            self.add_error(
                "date_debut_vote",
                "La période de vote doit commencer après la fin de la période 1."
            )

        return cleaned_data



class DemandeElecteurForm(forms.ModelForm):
    class Meta:
        model = DemandeElecteur
        fields = ["scrutin", "commentaire"]
        widgets = {"commentaire": forms.Textarea(attrs={"rows": 3, "placeholder": "Commentaire optionnel..."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commentaire"].required = False
        self.fields["scrutin"].queryset = Scrutin.objects.filter(statut="ouvert")


from django import forms

from vote.users.models import DemandeCandidature
from vote.users.models import Scrutin


class DemandeCandidatureForm(forms.ModelForm):
    class Meta:
        model = DemandeCandidature

        fields = [
            "scrutin",
            "slogan",
            "programme",
            "image",
            "commentaire",
        ]

        widgets = {
            "programme": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Présentez votre programme électoral...",
                    "class": "w-full",
                }
            ),

            "commentaire": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Lettre de motivation...",
                    "class": "w-full",
                }
            ),

            "slogan": forms.TextInput(
                attrs={
                    "placeholder": "Votre slogan...",
                    "class": "w-full",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["commentaire"].required = False
        self.fields["programme"].required = False
        self.fields["slogan"].required = False
        self.fields["image"].required = False

        self.fields["scrutin"].queryset = Scrutin.objects.filter(
            statut="ouvert"
        )

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if image:
            # max 5MB
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    "Image trop volumineuse (max 5MB)."
                )

            allowed_types = [
                "image/jpeg",
                "image/png",
                "image/webp",
            ]

            if image.content_type not in allowed_types:
                raise forms.ValidationError(
                    "Format image invalide."
                )

        return image