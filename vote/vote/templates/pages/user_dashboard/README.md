# 📊 Dashboard Utilisateur - Guide Complet

## 🎯 Vue d'ensemble

Le nouveau tableau de bord a été complètement restructuré en composants modulaires et maintenant affiche les **données réelles** de l'utilisateur connecté.

### Deux Modes d'Affichage

#### 1️⃣ **Mode Candidat**
- Affiche la carte de profil du candidat
- Statistiques complètes des votes
- Suivi de la campagne électorale
- Distribution des votes par filière et niveau

#### 2️⃣ **Mode Électeur**
- Affiche la carte de profil électeur
- Statistiques de participation
- Liste des scrutins complétés
- Taux de participation global

---

## 🏗️ Structure des Fichiers

```
/vote/templates/pages/user_dashboard/
├── user.html                          # Page principale (utilise les composants)
└── components/
    ├── sidebar.html                   # Navigation principale + profil
    ├── header.html                    # Header avec bienvenue + statut
    ├── candidat_card.html             # Carte profil candidat
    ├── electeur_card.html             # Carte profil électeur
    ├── candidat_statistics.html       # Stats complètes candidat
    ├── electeur_statistics.html       # Stats complètes électeur
    └── scrutins_section.html          # Liste scrutins accessibles
```

---

## 💾 Données Dynamiques Affichées

### User Data
```
- Prénom, Nom, Email
- Matricule
- Filière
- Niveau d'étude
- Photo (avatar si non définie)
- Rôle (Candidat/Électeur)
```

### Candidat Data
```
- Nombre total de votes
- Position/Ranking
- Pourcentage de progrès
- Votes par filière (graphique)
- Votes par niveau (graphique)
- Votes par jour de semaine
- Statut de candidature
```

### Électeur Data
```
- Nombre de votes participés
- Nombres de scrutins complétés
- Scrutins en cours
- Scrutins à venir
- Taux de participation
- Historique de participation
```

---

## 🎨 Design & Features

### ✨ Caractéristiques Visuelles
- **Couleurs**: Bleu professionnel (brand colors)
- **Typographie**: Plus Jakarta Sans (body), Instrument Serif (titres)
- **Spacing**: Design soft avec arrondi `rounded-2rem`
- **Ombres**: Subtiles `shadow-sm`, plus fortes au hover
- **Animations**: Transitions douces, hover effects

### 📱 Responsive Design
- **Desktop**: Sidebar fixe, layout 3+8 ou 4+8 colonnes
- **Tablet**: Sidebar masqué, grid responsive
- **Mobile**: Drawer sidebar avec backdrop, full width content

### 🔔 Statuts & Badges
```
Candidat Approuvé    ✓ Vert
Candidat En attente  ⏳ Jaune
Électeur Actif       • Bleu
```

---

## 🔧 Configuration Vue Django

La vue `UserDashboardView` récupère automatiquement:

```python
# Dans get_context_data():
- user              # Utilisateur connecté
- is_candidat       # Booléen
- candidat          # Objet Candidat ou None
- total_electeurs   # Total électeurs du scrutin
- ranking           # Position du candidat
- progress          # % de progression
- votes_by_filiere  # Distribution [(filiere, count, percentage), ...]
- votes_by_niveau   # Distribution [(niveau, count, percentage), ...]
- weekly_votes      # {'Lun': 0, 'Mar': 0, ...}
- vote_progress     # % depuis hier
- scrutins_accessibles  # QuerySet des scrutins accessibles
```

---

## 🚀 Accès au Dashboard

### URL
```
/user/dashboard/
```

### Authentification Requise
- Doit être connecté (utilise `LoginRequiredMixin`)
- Redirect vers `/users/login/` si non connecté

### Redirection Automatique
- Admin/Staff → Admin Dashboard
- Autres utilisateurs → User Dashboard

---

## 📋 Données en Temps Réel

Le tableau de bord affiche:
- ✓ Votes réels de la base de données
- ✓ Infos utilisateur actualisées
- ✓ Statut candidature à jour
- ✓ Progression calculée automatiquement
- ✓ Ranking parmi les autres candidats

### Calculs Effectués
```python
# Progrès candidat
progress = (votes / total_electeurs) * 100

# Classement
ranking = Position parmi tous les candidats du scrutin

# Distribution par filière/niveau
percentage = (votes_pour_filiere / total_votes) * 100

# Votes par jour
weekly_votes = Agrégation par jour de la semaine
```

---

## 🎯 Utilisation

### Pour un Candidat
1. Se connecte → Voit son dashboard candidat
2. Affichage:
   - Carte profil avec photo et stats
   - Progression des votes en graphique
   - Distribution par filière/niveau
   - Scrutins où il est électeur

### Pour un Électeur
1. Se connecte → Voit son dashboard électeur
2. Affichage:
   - Carte profil
   - Participation aux scrutins
   - Scrutins disponibles à voter

---

## 🔜 Prochaines Améliorations

- [ ] Page profil éditable
- [ ] Notifications réelles
- [ ] Export des statistiques (PDF)
- [ ] Historique d'activités complet
- [ ] Messages entre candidats/admins
- [ ] Paramètres utilisateur personnalisés
- [ ] Graphiques interactifs avec Charts.js

---

## 🐛 Dépannage

### Le dashboard est blanc
→ Vérifier que `is_candidat` est passé en contexte

### Les données ne s'affichent pas
→ Vérifier la base de données (votes existants)

### Photos ne s'affichent pas
→ Vérifier que `/media/` est configuré dans `settings.py`

### Mobile sidebar ne s'ouvre pas
→ Vérifier que JavaScript est activé

---

## 📞 Support

Pour questions ou bugs, consultez:
- Models: `/vote/users/models.py`
- Views: `/vote/users/views.py`
- Templates: `/vote/templates/pages/user_dashboard/`
