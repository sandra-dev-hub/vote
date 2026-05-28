# vote

Mon projet de vote
1)  Au démarrage
    • Lancer l’appli: uv run python manage.py runserver
        ◦ worker Celery: uv run celery -A config worker -l info
    • beat Celery: uv run celery -A config beat -l info

Parcours de l’utilisateur 
A. Créer un compte / se connecter
    • Aller dans  /users/register/ puis /users/login/.
B. Voir les scrutins disponibles
    • Va sur /scrutins/.
    • Tu verras les scrutins ouverts et dans la bonne période.
C. Devenir électeur pour un scrutin
    • Sur une carte scrutin, cliquer sur “Voter” (ça envoie une demande électeur).
    • Statut attendu ensuite: “Demande envoyée”.
D. Quand l’admin approuve
    • Le bouton devient “Accéder au vote” sur /scrutins/.
    • Clique dessus pour ouvrir la salle de vote: /users/scrutins/<slug>/vote/.
E. Voter
    • Dans vote_room:
      choisis un candidat,clique “Enregistrer mon vote”,Tu ne peux voter qu’une seule fois par scrutin.
Parcours Admin
A. Créer un scrutin
    • /users/admin/scrutins/
    • Renseigne titre + dates + statut.
B. Valider les électeurs
    • /users/admin/electeurs/demandes/
    • Cliquer et approuver pour autoriser le vote.
C. Suivre en direct
    • /users/admin/dashboard/
    • Bloc résultats live (WebSocket).
Quand on peut voter ?
Le vote est autorisé seulement si:
    • scrutin ouvert,
    • date actuelle >= date_debut,
    • date actuelle <= date_fin,
    • utilisateur validé comme électeur,
    • utilisateur n’a pas déjà voté.
Sinon, vote refusé côté backend.
Mot de passe oublié
    • Depuis login: clique OUBLIÉ ?
    • Flow: /users/password-reset/,mail reçu,lien reset,nouveau mot de passe,connexion.