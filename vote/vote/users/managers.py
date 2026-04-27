from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.hashers import make_password

from vote.global_data.enums import Role



class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        # pour gerer mon hash du mot de passe
        user.mot_de_passe = make_password(password)

        user.save(using=self._db)
        return user

    def create_admin(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        extra_fields.setdefault("is_admin", True)

        return self.create_user(email, password, **extra_fields)

