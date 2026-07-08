import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django_extensions.db.models import ActivatorModel, TimeStampedModel
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
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
    photo = models.ImageField(upload_to="utilisateurs/", null=True, blank=True)
    nom = models.CharField(max_length=100, null=True, blank=True)
    prenom = models.CharField(max_length=100, null=True, blank=True)
    filiere = models.CharField(max_length=100, null=True, blank=True)
    niveau = models.CharField(max_length=50, null=True, blank=True)
    biographie = models.TextField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
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
        return self.is_staff or self.role == Role.ADMIN

    def __str__(self):
        return f"{self.email} ({self.matricule})"


class Scrutin(BaseModel):
    titre = models.CharField(max_length=255)
    description = models.TextField()

    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    date_debut_vote = models.DateTimeField()
    date_fin_vote = models.DateTimeField()
    statut = models.CharField(
        max_length=50,
        choices=StatutScrutin.choices,
        default=StatutScrutin.OUVERT
    )

    slug = models.SlugField(unique=True)

    admin = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="scrutins"
    )

    class Meta:
        verbose_name = 'Scrutin'
        verbose_name_plural = 'Scrutins'

    def ouvrir(self):
        """Passe le scrutin en période 1 (candidatures & inscriptions)."""
        self.statut = StatutScrutin.OUVERT
        self.save()

    def passer_en_vote(self):
        """Passe le scrutin en période 2 (vote actif)."""
        self.statut = StatutScrutin.EN_VOTE
        self.save()

    def annuler(self):
        self.statut = StatutScrutin.ANNULE
        self.save()

    def cloturer(self):
        self.statut = StatutScrutin.FERME
        self.save()

    def __str__(self):
        return self.titre

    def est_periode_candidature(self):
        """Retourne True si on est en période 1 : dépôt des candidatures et demandes électeur."""
        now = timezone.now()
        return (
            self.statut == StatutScrutin.OUVERT
            and self.date_debut <= now <= self.date_fin
        )

    def est_periode_vote(self):
        """Retourne True si on est en période 2 : vote actif."""
        now = timezone.now()
        # Accept voting when either the status is explicitly EN_VOTE
        # or when the vote dates indicate we are in the voting window.
        in_date_window = self.date_debut_vote <= now <= self.date_fin_vote
        return (self.statut == StatutScrutin.EN_VOTE and in_date_window) or in_date_window

    def is_open_for_vote(self):
        """Alias pour est_periode_vote() — compatibilité ascendante."""
        return self.est_periode_vote()


class DemandeElecteur(BaseModel):
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="demande_electeur"
    )

    scrutin = models.ForeignKey(
        Scrutin,
        on_delete=models.CASCADE,
        related_name="demandes_electeur"
    )

    statut = models.CharField(
    max_length=50,
    choices=StatutDemande.choices,
    default=StatutDemande.EN_ATTENTE
    )

    date_soumission = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    commentaire = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'DemandeElecteur'
        verbose_name_plural = 'DemandeElecteurs'
    
    def __str__(self):  
        return f"{self.utilisateur.email}"



class Electeur(BaseModel):
    demande = models.OneToOneField( 
        DemandeElecteur,
        on_delete=models.CASCADE,
        related_name="electeur"
    )

    scrutin = models.ForeignKey(
        Scrutin,
        on_delete=models.CASCADE,
        related_name="electeurs"
    )

    date_inscription = models.DateTimeField(auto_now_add=True)
    notification_ouverture_envoyee = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Electeur'
        verbose_name_plural = 'Electeurs'

    def __str__(self):
        return f"{self.demande.utilisateur.email} - {self.scrutin.titre}"
    

class DemandeCandidature(BaseModel):
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="demande_candidature"
    )
    statut = models.CharField(
        max_length=50,
        choices=StatutDemande.choices,
        default=StatutDemande.EN_ATTENTE
    )
    scrutin = models.ForeignKey(
        Scrutin,
        on_delete=models.CASCADE,
        related_name="demandes_candidature"
    )
    date_soumission = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    commentaire = models.TextField(null=True, blank=True)
    programme = models.TextField(null=True, blank=True)
    slogan = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to="candidatures/", null=True, blank=True)


    class Meta:
        verbose_name = 'DemandeCandidature'
        verbose_name_plural = 'DemandeCandidatures'


class Candidat(BaseModel):
    demande = models.OneToOneField( 
        DemandeCandidature,
        on_delete=models.CASCADE,
        related_name="candidat"
    )
    scrutin = models.ForeignKey(
        Scrutin,
        on_delete=models.CASCADE,
        related_name="candidats",
        null=True,
        blank=True
    )
    nombre_vote = models.PositiveIntegerField(default=0)

    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Candidat'
        verbose_name_plural = 'Candidats'

    def __str__(self):
        return f"{self.demande.utilisateur.nom} {self.demande.utilisateur.prenom} - {self.scrutin.titre}"

    def get_pourcentage(self):
        total_votes = self.demande.scrutin.votes_candidat.count()
        if total_votes == 0:
            return 0
        return round((self.nombre_vote / total_votes) * 100, 2)



class Vote(BaseModel):
    horodatage = models.DateTimeField(auto_now_add=True)
    adresse_ip = models.GenericIPAddressField()

    electeur = models.OneToOneField( 
        Electeur,
        on_delete=models.CASCADE,
        related_name="votes_electeur"
    )

    candidat = models.ForeignKey(
        Candidat,
        on_delete=models.CASCADE,
        related_name="votes_candidat"
    )

    class Meta:
        verbose_name = 'Vote'
        verbose_name_plural = 'Votes'

    def clean(self):
        # Empêche incohérence scrutin
        if self.candidat.scrutin_id != self.electeur.scrutin_id:
            raise ValidationError("Le candidat n'appartient pas au scrutin de l'électeur.")

        scrutin = self.electeur.scrutin
        now = timezone.now()

        # Vérifier que le scrutin est bien en période de VOTE (période 2)
        # Use the `est_periode_vote` helper which considers the vote date window.
        if not scrutin.est_periode_vote():
            raise ValidationError("Ce scrutin n'est pas en période de vote.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

        #  incrément automatique
        self.candidat.nombre_vote += 1
        self.candidat.save()




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


User = Utilisateur

