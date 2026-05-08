from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from allauth.account.decorators import secure_admin_login

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import (
    Utilisateur, 
    Scrutin, 
    DemandeElecteur, 
    DemandeCandidature, 
    Electeur, 
    Candidat, 
    Vote
)


if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    admin.autodiscover()
    admin.site.login = secure_admin_login(admin.site.login)


@admin.register(Utilisateur)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    list_display = ("email", "matricule", "role", "is_staff", "is_active", "is_verified")
    list_filter = ("role", "is_staff", "is_active", "is_verified")
    search_fields = ("email", "matricule", "nom", "prenom")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Informations personnelles"), {
            "fields": ("matricule", "nom", "prenom", "filiere", "niveau", "age", "telephone", "photo", "biographie")
        }),
        (_("Rôle et Permissions"), {
            "fields": ("role", "is_active", "is_staff", "is_superuser", "is_verified", "groups", "user_permissions"),
        }),
        (_("Dates importantes"), {"fields": ("last_login", "created", "modified")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "matricule", "password1", "password2", "role", "is_staff", "is_active"),
        }),
    )

    readonly_fields = ("created", "modified")


# Enregistrement des autres modèles
@admin.register(Scrutin)
class ScrutinAdmin(admin.ModelAdmin):
    list_display = ("titre", "statut", "date_debut", "date_fin", "admin")
    list_filter = ("statut",)
    search_fields = ("titre", "description")
    ordering = ("-created",)


@admin.register(DemandeElecteur)
class DemandeElecteurAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "scrutin", "statut", "date_soumission")
    list_filter = ("statut", "scrutin")
    search_fields = ("utilisateur__email", "commentaire")


@admin.register(DemandeCandidature)
class DemandeCandidatureAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "scrutin", "statut", "date_soumission")
    list_filter = ("statut", "scrutin")
    search_fields = ("utilisateur__email", "commentaire")


admin.site.register(Electeur)
admin.site.register(Candidat)
admin.site.register(Vote)