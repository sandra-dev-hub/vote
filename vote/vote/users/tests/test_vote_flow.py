from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from vote.users.models import Utilisateur, Scrutin, DemandeElecteur, Electeur, Candidat, DemandeCandidature, Vote
from vote.global_data.enums import StatutScrutin, StatutDemande
from django.core.exceptions import ValidationError
import datetime

class VoteFlowTests(TestCase):
    def setUp(self):
        # utilisateur
        self.user = Utilisateur.objects.create_user(email='user@example.com', password='pass')
        # admin
        self.admin = Utilisateur.objects.create_user(email='admin@example.com', password='pass', is_staff=True)

        now = timezone.now()
        # créer un scrutin avec des périodes précises
        self.scrutin = Scrutin.objects.create(
            titre='Test',
            description='desc',
            date_debut=now - datetime.timedelta(minutes=10),
            date_fin=now - datetime.timedelta(minutes=5),
            date_debut_vote=now + datetime.timedelta(minutes=5),
            date_fin_vote=now + datetime.timedelta(minutes=10),
            statut=StatutScrutin.OUVERT,
            slug='test-scrutin',
            admin=self.admin,
        )

        # créer candidat pour le scrutin
        demande = DemandeCandidature.objects.create(utilisateur=self.admin, scrutin=self.scrutin, statut=StatutDemande.APPROUVE)
        self.candidat = Candidat.objects.create(demande=demande, scrutin=self.scrutin, slug='c1')

    def test_candidature_period_can_submit_electeur_request(self):
        # période candidature (date_debut..date_fin) in our setup is now-10..now-5 -> in past, adjust to be inside
        self.scrutin.date_debut = timezone.now() - datetime.timedelta(minutes=2)
        self.scrutin.date_fin = timezone.now() + datetime.timedelta(minutes=2)
        self.scrutin.save()

        self.client.login(email='user@example.com', password='pass')
        resp = self.client.post(reverse('users:scrutins'), data={'type_demande': 'electeur', 'scrutin_id': str(self.scrutin.pk)})
        self.assertEqual(DemandeElecteur.objects.filter(utilisateur=self.user, scrutin=self.scrutin).count(), 1)

    def test_waiting_period_shows_in_list_and_prevents_voting(self):
        # set periods: end of depot in past, vote start in future -> waiting
        now = timezone.now()
        self.scrutin.date_debut = now - datetime.timedelta(minutes=20)
        self.scrutin.date_fin = now - datetime.timedelta(minutes=10)
        self.scrutin.date_debut_vote = now + datetime.timedelta(minutes=5)
        self.scrutin.date_fin_vote = now + datetime.timedelta(minutes=15)
        self.scrutin.statut = StatutScrutin.EN_VOTE
        self.scrutin.save()

        # approve electeur via Demande -> Electeur exists
        demande = DemandeElecteur.objects.create(utilisateur=self.user, scrutin=self.scrutin, statut=StatutDemande.APPROUVE)
        Electeur.objects.create(demande=demande, scrutin=self.scrutin)

        # user can access scrutins page and see the scrutin
        self.client.login(email='user@example.com', password='pass')
        resp = self.client.get(reverse('users:scrutins'))
        self.assertContains(resp, 'En attente d\'ouverture', msg_prefix='Scrutin should show waiting state')

        # try to post a vote (should be prevented by ScrutinVoteView)
        resp = self.client.post(reverse('users:scrutin_vote', kwargs={'slug': self.scrutin.slug}), data={'candidat_slug': self.candidat.slug})
        # after redirect, no Vote created
        self.assertEqual(Vote.objects.filter(electeur__scrutin=self.scrutin).count(), 0)

    def test_vote_period_allows_vote_and_blocks_second_vote(self):
        now = timezone.now()
        self.scrutin.statut = StatutScrutin.EN_VOTE
        self.scrutin.date_debut_vote = now - datetime.timedelta(minutes=1)
        self.scrutin.date_fin_vote = now + datetime.timedelta(minutes=10)
        self.scrutin.save()

        demande = DemandeElecteur.objects.create(utilisateur=self.user, scrutin=self.scrutin, statut=StatutDemande.APPROUVE)
        electeur = Electeur.objects.create(demande=demande, scrutin=self.scrutin)

        self.client.login(email='user@example.com', password='pass')
        resp = self.client.post(reverse('users:scrutin_vote', kwargs={'slug': self.scrutin.slug}), data={'candidat_slug': self.candidat.slug})
        self.assertEqual(Vote.objects.filter(electeur=electeur).count(), 1)

        # try voting again
        resp = self.client.post(reverse('users:scrutin_vote', kwargs={'slug': self.scrutin.slug}), data={'candidat_slug': self.candidat.slug})
        self.assertEqual(Vote.objects.filter(electeur=electeur).count(), 1)
*** End Patch