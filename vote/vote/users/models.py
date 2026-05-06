import uuid
from django.db import models
from django_extensions.db.models import ActivatorModel, TimeStampedModel
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from vote.global_data.enums import Role, StatutDemande, StatutScrutin
from vote.users.managers import UserManager


class BaseModel(TimeStampedModel, ActivatorModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Utilisateur(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True)
    matricule = models.CharField(max_length=50, unique=True, null=True, blank=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ELECTEUR
    )

    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "utilisateurs"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["matricule"]),
        ]

    def is_admin(self):
        return self.is_staff or self.is_superuser or self.role == Role.ADMIN

    def __str__(self):
        return f"{self.email} ({self.matricule})"


class Administrateur(Utilisateur):
    nom_admin = models.CharField(max_length=100)
    prenom_admin = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Administrateur'
        verbose_name_plural = 'Administrateurs'

    def creer_scrutin(self):
        pass

    def publier_resultat(self):
        pass


class Scrutin(BaseModel):
    titre = models.CharField(max_length=255)
    description = models.TextField()

    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()

    statut = models.CharField(
        max_length=50,
        choices=StatutScrutin.choices,
        default=StatutScrutin.OUVERT
    )

    slug = models.SlugField(unique=True)

    admin = models.ForeignKey(
        Administrateur,
        on_delete=models.CASCADE,
        related_name="scrutins"
    )

    class Meta:
        verbose_name = 'Scrutin'
        verbose_name_plural = 'Scrutins'

    def ouvrir(self):
        self.statut = StatutScrutin.OUVERT
        self.save()

    def annuler(self):
        self.statut = StatutScrutin.ANNULE
        self.save()

    def cloturer(self):
        self.statut = StatutScrutin.CLOTURE
        self.save()



class Electeur(BaseModel):
    matricule = models.CharField(max_length=50)
    filiere = models.CharField(max_length=100)
    niveau = models.CharField(max_length=50)

    nom_elec = models.CharField(max_length=100)
    prenom_elec = models.CharField(max_length=100)

    scrutin = models.ForeignKey(
        Scrutin,
        on_delete=models.CASCADE,
        related_name="electeurs"
    )

    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('matricule', 'scrutin')
        verbose_name = 'Electeur'
        verbose_name_plural = 'Electeurs'

    def __str__(self):
        return f"{self.nom_elec} {self.prenom_elec} - {self.scrutin.titre}"
    
    class DemandeElecteur(BaseModel):
        biographie = models.TextField()
        photo = models.ImageField(upload_to="demandes/", null=True, blank=True)

        age = models.PositiveIntegerField()

        matricule = models.CharField(max_length=50)
        filiere = models.CharField(max_length=100)

        nom = models.CharField(max_length=100)
        prenom = models.CharField(max_length=100)
        niveau = models.CharField(max_length=50)

        statut = models.CharField(
        max_length=50,
        choices=StatutDemande.choices,
        default=StatutDemande.EN_ATTENTE
        )

        date_soumission = models.DateTimeField(auto_now_add=True)
        date_traitement = models.DateTimeField(null=True, blank=True)

  
    class Meta:
        unique_together = ('matricule', 'scrutin')
        verbose_name = 'DemandeCandidature'
        verbose_name_plural = 'DemandeCandidatures'



class Candidat(BaseModel):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)

    description = models.TextField()
    photo = models.ImageField(upload_to="candidats/", null=True, blank=True)

    matricule = models.CharField(max_length=50)
    filiere = models.CharField(max_length=100)
    niveau = models.CharField(max_length=50)

    nb_vote = models.PositiveIntegerField(default=0)

    slug = models.SlugField(unique=True)

    scrutin = models.ForeignKey(
        Scrutin,
        on_delete=models.CASCADE,
        related_name="candidats"
    )

    class Meta:
        unique_together = ('matricule', 'scrutin')
        verbose_name = 'Candidat'
        verbose_name_plural = 'Candidats'

    def __str__(self):
        return f"{self.nom} {self.prenom} - {self.scrutin.titre}"

    def get_pourcentage(self):
        total_votes = self.scrutin.votes.count()
        if total_votes == 0:
            return 0
        return round((self.nb_vote / total_votes) * 100, 2)



class Vote(BaseModel):
    horodatage = models.DateTimeField(auto_now_add=True)
    adresse_ip = models.GenericIPAddressField()

    electeur = models.ForeignKey(
        Electeur,
        on_delete=models.CASCADE,
        related_name="votes"
    )

    candidat = models.ForeignKey(
        Candidat,
        on_delete=models.CASCADE,
        related_name="votes"
    )

    scrutin = models.ForeignKey(
        Scrutin,
        on_delete=models.CASCADE,
        related_name="votes"
    )

    class Meta:
        unique_together = ('electeur', 'scrutin')
        verbose_name = 'Vote'
        verbose_name_plural = 'Votes'

    def clean(self):
        # 🔥 Empêche incohérence scrutin
        if self.candidat.scrutin_id != self.scrutin_id:
            raise ValueError("Le candidat n'appartient pas à ce scrutin")

        if self.electeur.scrutin_id != self.scrutin_id:
            raise ValueError("L'électeur n'appartient pas à ce scrutin")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

        # 🔥 incrément automatique
        self.candidat.nb_vote += 1
        self.candidat.save()



class DemandeCandidature(BaseModel):
    biographie = models.TextField()
    photo = models.ImageField(upload_to="demandes/", null=True, blank=True)

    age = models.PositiveIntegerField()

    matricule = models.CharField(max_length=50)
    filiere = models.CharField(max_length=100)

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    niveau = models.CharField(max_length=50)

    statut = models.CharField(
        max_length=50,
        choices=StatutDemande.choices,
        default=StatutDemande.EN_ATTENTE
    )

    date_soumission = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)

    commentaire = models.TextField(null=True, blank=True)

    scrutin = models.ForeignKey(
        Scrutin,
        on_delete=models.CASCADE,
        related_name="demandes"
    )

    admin = models.ForeignKey(
        Administrateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('matricule', 'scrutin')
        verbose_name = 'DemandeCandidature'
        verbose_name_plural = 'DemandeCandidatures'



class Logaudit(BaseModel):
    action = models.CharField(max_length=50)
    adresse_ip = models.GenericIPAddressField()
    horodatage = models.DateTimeField(auto_now_add=True)
    detail = models.TextField(null=True, blank=True)

    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="logs"
    )

    class Meta:
        verbose_name = 'Logaudit'
        verbose_name_plural = 'Logaudits'

    def __str__(self):
        return f"{self.action} - {self.horodatage}"