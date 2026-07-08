import pytest
from django.urls import reverse

from vote.users.models import Logaudit


@pytest.mark.django_db
def test_profile_update_creates_audit_log(client, user):
    client.force_login(user)

    response = client.post(
        reverse("users:profile"),
        {
            "prenom": "Ada",
            "nom": "Lovelace",
            "filiere": "Informatique",
            "niveau": "L3",
            "telephone": "690000000",
            "biographie": "Profil mis à jour",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert Logaudit.objects.filter(utilisateur=user, action="profile_updated").exists()


@pytest.mark.django_db
def test_audit_log_page_requires_admin(client, user):
    """Test que la page logaudit redirige les utilisateurs non-admin."""
    client.force_login(user)
    response = client.get(reverse("users:logaudit"))

    assert response.status_code == 302
    assert response.url == reverse("users:user_dashboard")


@pytest.mark.django_db
def test_audit_log_page_lists_all_events_for_admin(client, admin_user):
    """Test que la page logaudit affiche tous les événements pour un admin."""
    Logaudit.objects.create(
        utilisateur=admin_user,
        action="profile_updated",
        adresse_ip="127.0.0.1",
        detail="Profil admin mis à jour",
    )

    client.force_login(admin_user)
    response = client.get(reverse("users:logaudit"))

    assert response.status_code == 200
    assert "Profil admin mis à jour" in response.content.decode()
