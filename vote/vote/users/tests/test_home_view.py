from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from vote.global_data.enums import Role, StatutScrutin
from vote.users.models import Candidat, DemandeCandidature, Scrutin, Utilisateur


class HomeViewTests(TestCase):
    def test_home_view_uses_nearest_scrutin_for_carousel(self):
        admin = Utilisateur.objects.create_user(
            email="admin@example.com",
            password="secret123",
            role=Role.ADMIN,
            is_staff=True,
        )

        now = timezone.now()
        past_scrutin = Scrutin.objects.create(
            titre="Ancien scrutin",
            description="Ancien",
            date_debut=now - timedelta(days=40),
            date_fin=now - timedelta(days=30),
            date_debut_vote=now - timedelta(days=30),
            date_fin_vote=now - timedelta(days=20),
            statut=StatutScrutin.FERME,
            slug="ancien-scrutin",
            admin=admin,
        )
        nearest_scrutin = Scrutin.objects.create(
            titre="Scrutin proche",
            description="À venir",
            date_debut=now + timedelta(days=3),
            date_fin=now + timedelta(days=12),
            date_debut_vote=now + timedelta(days=3),
            date_fin_vote=now + timedelta(days=12),
            statut=StatutScrutin.OUVERT,
            slug="scrutin-proche",
            admin=admin,
        )

        user = Utilisateur.objects.create_user(
            email="candidat@example.com",
            password="secret123",
            role=Role.ELECTEUR,
            nom="Doe",
            prenom="Jane",
            filiere="Informatique",
        )

        demande = DemandeCandidature.objects.create(
            utilisateur=user,
            scrutin=nearest_scrutin,
            statut="accepte",
            programme="Programme test",
            slogan="Un candidat",
        )
        Candidat.objects.create(
            demande=demande,
            scrutin=nearest_scrutin,
            slug="jane-doe",
        )

        DemandeCandidature.objects.create(
            utilisateur=Utilisateur.objects.create_user(
                email="oldcandidat@example.com",
                password="secret123",
                role=Role.ELECTEUR,
                nom="Old",
                prenom="Candidate",
            ),
            scrutin=past_scrutin,
            statut="accepte",
            programme="Ancien programme",
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.context["scrutin"], nearest_scrutin)
        self.assertEqual(len(response.context["carousel_candidates"]), 1)
        self.assertEqual(response.context["carousel_candidates"][0]["name"], "Doe Jane")

    def test_home_view_prefers_scrutin_with_candidates_when_closest_scrutin_is_empty(self):
        admin = Utilisateur.objects.create_user(
            email="admin2@example.com",
            password="secret123",
            role=Role.ADMIN,
            is_staff=True,
        )

        now = timezone.now()
        empty_scrutin = Scrutin.objects.create(
            titre="Scrutin vide",
            description="Plus proche",
            date_debut=now + timedelta(days=1),
            date_fin=now + timedelta(days=2),
            date_debut_vote=now + timedelta(days=1),
            date_fin_vote=now + timedelta(days=2),
            statut=StatutScrutin.OUVERT,
            slug="scrutin-vide",
            admin=admin,
        )
        populated_scrutin = Scrutin.objects.create(
            titre="Scrutin avec candidats",
            description="Plus loin",
            date_debut=now + timedelta(days=3),
            date_fin=now + timedelta(days=8),
            date_debut_vote=now + timedelta(days=3),
            date_fin_vote=now + timedelta(days=8),
            statut=StatutScrutin.OUVERT,
            slug="scrutin-avec-candidats",
            admin=admin,
        )

        user = Utilisateur.objects.create_user(
            email="candidat2@example.com",
            password="secret123",
            role=Role.ELECTEUR,
            nom="Smith",
            prenom="John",
            filiere="Gestion",
        )

        demande = DemandeCandidature.objects.create(
            utilisateur=user,
            scrutin=populated_scrutin,
            statut="accepte",
            programme="Programme test",
            slogan="Un candidat",
        )
        Candidat.objects.create(
            demande=demande,
            scrutin=populated_scrutin,
            slug="john-smith",
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.context["scrutin"], populated_scrutin)
        self.assertEqual(len(response.context["carousel_candidates"]), 1)
        self.assertEqual(response.context["carousel_candidates"][0]["name"], "Smith John")
