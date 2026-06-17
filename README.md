# vote — instructions locales complètes

Ce fichier décrit les commandes nécessaires pour exécuter le projet en local, comment accéder aux pages importantes (dont la salle de vote), et les services auxiliaires (SMTP, Celery).

Prérequis
- Python 3.10+ (venv recommandé)
- Redis (si vous utilisez Celery avec broker redis)
- (Optionnel) Docker pour Mailhog

Installation et démarrage rapide
--------------------------------
Exécutez depuis la racine du dépôt (là où se trouve `manage.py`):

```bash
cd vote

# 1) Créer et activer le venv
python -m venv .venv
source .venv/bin/activate

# 2) Installer les dépendances
pip install -r requirements.txt

# 3) Variables d'environnement (exemple minimal pour dev)
export DJANGO_SECRET_KEY='change_me'
export DJANGO_DEBUG=True
export DJANGO_EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'
export DJANGO_DEFAULT_FROM_EMAIL='noreply@icab.local'

# 4) Appliquer les migrations
./.venv/bin/python manage.py migrate

# 5) (Optionnel) Créer un superuser
./.venv/bin/python manage.py createsuperuser

# 6) Collectstatic (nécessaire pour WhiteNoise/static files)
./.venv/bin/python manage.py collectstatic --noinput

# 7) Lancer le serveur de développement
./.venv/bin/python manage.py runserver 0.0.0.0:8001
```

Accès aux routes principales (exemples)
- Accueil : http://localhost:8001/
- Liste des scrutins (utilisateur) : http://localhost:8001/scrutins/
- Tableau de bord utilisateur : http://localhost:8001/users/dashboard/
- Admin Django : http://localhost:8001{{ settings.ADMIN_URL }} (ou /admin/ si non modifié)
- Salle de vote (vote_room) : http://localhost:8001/users/scrutins/<slug>/vote/  (remplacez `<slug>` par le slug du scrutin)

Lister les slugs de scrutins depuis la console (utile pour tester la `vote_room`):

```bash
./.venv/bin/python manage.py shell -c "from vote.users.models import Scrutin; print([s.slug for s in Scrutin.objects.all()])"
```

Tester la salle de vote (rapide)
- Connectez-vous avec un compte utilisateur.
- Assurez-vous que le `Scrutin` est en période de vote (`statut == EN_VOTE` et `date_debut_vote <= now <= date_fin_vote`).
- Si vous n'êtes pas inscrit comme `Electeur` pour ce scrutin, créez une `DemandeElecteur` (via UI ou admin) et faites approuver côté admin.
- Ouvrez `http://localhost:8001/users/scrutins/<slug>/vote/` pour voir la `vote_room`.

SMTP local (voir les options)
--------------------------------
Option A — Mailhog (recommandé pour dev, Docker)

```bash
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
```
Puis dans votre environnement :

```bash
export DJANGO_EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
export DJANGO_EMAIL_HOST='127.0.0.1'
export DJANGO_EMAIL_PORT=1025
export DJANGO_EMAIL_USE_TLS=False
export DJANGO_DEFAULT_FROM_EMAIL='noreply@icab.local'
```
Ouvrez l'interface Mailhog : http://localhost:8025

Option B — aiosmtpd (si Docker indisponible)

```bash
# installez si nécessaire
./.venv/bin/pip install aiosmtpd

# lancer le serveur debug SMTP qui affiche les mails reçus
./.venv/bin/python -m aiosmtpd -n -l 127.0.0.1:1025
```

Celery (tâches asynchrones)
---------------------------
Si votre projet utilise Celery (notifications etc.), démarrez Redis (broker) puis exécutez :

```bash
# dans un terminal (venv activé)
./.venv/bin/celery -A config worker -l info

# (optionnel) scheduler
./.venv/bin/celery -A config beat -l info
```

Collectstatic & WhiteNoise
--------------------------
Si vous servez des assets statiques via WhiteNoise en production locale, exécutez :

```bash
./.venv/bin/python manage.py collectstatic --noinput
```

Tests
-----
Lancer la suite de tests Django :

```bash
./.venv/bin/python manage.py test
```

Dépannage rapide
- Si vous voyez une erreur SMTP AUTH (SMTPNotSupportedError), utilisez Mailhog/aiosmtpd sans authentification (ne mettez pas DJANGO_EMAIL_HOST_USER/DJANGO_EMAIL_HOST_PASSWORD vides).
- Si `runserver` affiche `DisallowedHost`, lancez avec `--settings=config.settings.local` ou ajoutez `ALLOWED_HOSTS` dans votre env.

Notes sur l'interface et accès
--------------------------------
- Les cartes candidats sur l'accueil ont maintenant un bouton "Aller au vote" pointant vers la `vote_room` du scrutin correspondant.
- Depuis un profil candidat (page de détail), il existe aussi un bouton "Aller au vote".
- La route Django utilisée pour la salle de vote est nommée `users:scrutin_vote`.

Si vous voulez, je peux :
- Lancer `collectstatic` et vérifier les pages dans un navigateur headless,
- Ajouter des vérifications pour masquer le bouton "Aller au vote" quand l'utilisateur n'est pas électeur (actuellement le lien est visible). 

---

Commandes complètes pour démarrer tout en local (Node/npm, Redis, Celery, Mailhog)
--------------------------------------------------------------------------

1) Préparez l'environnement Python

```bash
cd vote
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Installer et builder les assets front-end (Tailwind / output.css)

# Le projet contient un `package.json` dans `vote/static/css` pour Tailwind.
```bash
# depuis la racine du repo
cd vote/vote/static/css
npm install        # installe les dépendances Node (Tailwind, autoprefixer, etc.)
npm run build      # produit `output.css` dans le même dossier (pour la prod)
# ou en développement
npm run watch      # recompilation à la volée pendant le dev
```

3) Variables d'environnement essentielles (exemple)

```bash
export DJANGO_SECRET_KEY='change_me'
export DJANGO_DEBUG=True
export DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1'
export DJANGO_DEFAULT_FROM_EMAIL='noreply@icab.local'
# Email (si vous utilisez Mailhog/aiosmtpd)
export DJANGO_EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
export DJANGO_EMAIL_HOST='127.0.0.1'
export DJANGO_EMAIL_PORT=1025
export DJANGO_EMAIL_USE_TLS=False
```

4) Base de données & migrations

```bash
# appliquez les migrations
./.venv/bin/python manage.py migrate

# (optionnel) créez un superutilisateur
./.venv/bin/python manage.py createsuperuser
```

5) Démarrer les services auxiliaires

# Redis (broker pour Celery) — si vous utilisez Redis :
```bash
# local (si installé sur la machine)
redis-server &

# ou via Docker
docker run -d --name redis -p 6379:6379 redis
```

# Mailhog (voir les mails via http://localhost:8025)
```bash
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
# ou si Docker absent : aiosmtpd
./.venv/bin/pip install aiosmtpd
./.venv/bin/python -m aiosmtpd -n -l 127.0.0.1:1025
```

6) Collectstatic (WhiteNoise)

```bash
./.venv/bin/python manage.py collectstatic --noinput
```

7) Lancer Celery (si utilisé)

```bash
# worker (venv activé)
./.venv/bin/celery -A config worker -l info

# scheduler (optionnel)
./.venv/bin/celery -A config beat -l info
```

8) Lancer le serveur Django

```bash
./.venv/bin/python manage.py runserver 0.0.0.0:8001
```

9) Commandes utiles

- Lister les scrutins et leurs slugs (pratique pour ouvrir la `vote_room`) :
```bash
./.venv/bin/python manage.py shell -c "from vote.users.models import Scrutin; print([s.slug for s in Scrutin.objects.all()])"
```
- Lancer les tests :
```bash
./.venv/bin/python manage.py test
```

10) Accès rapides après démarrage

- Accueil : http://localhost:8001/
- Scrutins (utilisateurs) : http://localhost:8001/scrutins/
- Salle de vote (vote_room) : http://localhost:8001/users/scrutins/<slug>/vote/
- Tableau de bord utilisateur : http://localhost:8001/users/dashboard/
- Admin Django : http://localhost:8001/admin/ (ou l'URL définie dans `settings.ADMIN_URL`)
- Mailhog UI : http://localhost:8025 (si vous utilisez Mailhog)

Notes et conseils
- Si vous utilisez un backend SMTP public (Gmail, Mailtrap), renseignez `DJANGO_EMAIL_HOST_USER` et `DJANGO_EMAIL_HOST_PASSWORD`.
- N'exposez jamais `DJANGO_SECRET_KEY` en clair en production.
- Si vous avez des erreurs `SMTPNotSupportedError` lorsque vous envoyez des emails vers un serveur debug, préférez Mailhog ou `aiosmtpd` (ils n'utilisent pas AUTH).

<!-- commande importantes: -->
uv run python manage.py runserver

npm run dev

<!-- pour lancer celery -->
uv run celery -A config beat -l info

uv run celery -A config worker -l info