# OpsDesk

OpsDesk est une application interne de gestion de tickets de support IT, conçue pour une petite équipe technique. Les utilisateurs peuvent soumettre des demandes (matériel, réseau, accès, sécurité, etc.) et les techniciens peuvent les prendre en charge, les prioriser et suivre leur résolution.

## Fonctionnalités

- Création, consultation, modification et suppression de tickets
- Gestion du statut (`Open`, `In Progress`, `Waiting`, `Resolved`, `Closed`) et de la priorité (`Low`, `Medium`, `High`, `Critical`)
- Catégorisation des tickets (`Hardware`, `Software`, `Network`, `Access`, `Security`, `Other`)
- Assignation des tickets à un technicien
- Commentaires sur chaque ticket
- Recherche et filtrage (titre, statut, priorité, catégorie, technicien)
- Tableau de bord avec statistiques (total, ouverts, en cours, critiques, résolus, répartitions)
- Authentification par session avec deux rôles : `user` et `technician`
- API REST JSON en plus de l'interface web
- Endpoint `/api/health` pour les vérifications de disponibilité
- Logs applicatifs écrits vers stdout/stderr

## Architecture de l'application

```
Navigateur
    │
    ▼
Flask (Blueprints)
 ├── auth.py     → authentification (login/logout, hashing, rôles)
 ├── routes.py   → vues HTML (dashboard, tickets, formulaires)
 └── api.py      → API REST JSON
    │
    ▼
SQLAlchemy (models.py)
    │
    ▼
PostgreSQL
```

L'application suit une architecture en couches simple :

- **Présentation** : templates Jinja2 + Bootstrap (`templates/`, `static/`)
- **Logique applicative** : blueprints Flask (`app/routes.py`, `app/api.py`, `app/auth.py`)
- **Accès aux données** : modèles SQLAlchemy (`app/models.py`) et instance `db` partagée (`app/database.py`)
- **Configuration** : entièrement pilotée par variables d'environnement (`app/config.py`)

## Stack technique

| Composant       | Technologie              |
|-----------------|---------------------------|
| Langage          | Python 3                 |
| Framework web    | Flask                    |
| ORM              | SQLAlchemy (Flask-SQLAlchemy) |
| Base de données  | PostgreSQL                |
| Frontend         | HTML, CSS, Bootstrap 5, JavaScript léger |
| Tests            | pytest                    |
| Authentification | Sessions Flask + hashing Werkzeug |

## Prérequis

- Python 3.10 ou supérieur
- PostgreSQL 13 ou supérieur
- `pip` et `venv` (inclus avec Python)

## Installation de Python

Vérifiez que Python 3 est installé :

```bash
python3 --version
```

Si nécessaire, installez-le depuis [python.org](https://www.python.org/downloads/) ou via le gestionnaire de paquets de votre système.

## Installation de PostgreSQL

### macOS (Homebrew)

```bash
brew install postgresql@16
brew services start postgresql@16
```

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Windows

Téléchargez l'installeur depuis [postgresql.org/download](https://www.postgresql.org/download/windows/) et suivez l'assistant.

## Création de la base de données

Connectez-vous à PostgreSQL :

```bash
psql -U postgres
```

Puis créez l'utilisateur, la base de développement et la base de test :

```sql
CREATE USER opsdesk_user WITH PASSWORD 'change-me';
CREATE DATABASE opsdesk OWNER opsdesk_user;
CREATE DATABASE opsdesk_test OWNER opsdesk_user;
\q
```

Les tables sont créées automatiquement par l'application au premier démarrage (via `db.create_all()`), aucune migration manuelle n'est requise pour ce projet.

## Configuration des variables d'environnement

Copiez le fichier d'exemple :

```bash
cp .env.example .env
```

Puis éditez `.env` avec vos propres valeurs :

```text
DATABASE_URL=postgresql://opsdesk_user:change-me@localhost:5432/opsdesk
SECRET_KEY=une-valeur-secrete-aleatoire
APP_ENV=development
PORT=5000
TEST_DATABASE_URL=postgresql://opsdesk_user:change-me@localhost:5432/opsdesk_test
```

⚠️ Ne committez jamais le fichier `.env` (il est déjà exclu via `.gitignore`).

## Installation des dépendances

Créez un environnement virtuel et installez les dépendances :

```bash
python3 -m venv .venv
source .venv/bin/activate        # Sous Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Lancement de l'application

Chargez les variables d'environnement puis démarrez le serveur :

```bash
export $(grep -v '^#' .env | xargs)   # Sous Windows : utilisez un outil comme python-dotenv ou définissez les variables manuellement
python run.py
```

L'application est alors accessible sur [http://localhost:5000](http://localhost:5000).

Au premier démarrage, des comptes et tickets de démonstration sont automatiquement créés :

| Utilisateur    | Rôle       | Mot de passe   |
|----------------|------------|----------------|
| alice          | user       | password123    |
| bob            | user       | password123    |
| tania.tech     | technician | password123    |
| marc.tech      | technician | password123    |

## Lancement des tests

Les tests utilisent une base de données séparée (`TEST_DATABASE_URL`) afin de ne jamais modifier les données de développement :

```bash
export APP_ENV=testing
pytest
```

Ou en une seule commande :

```bash
APP_ENV=testing pytest -v
```

## Endpoints API

| Méthode | Endpoint             | Description                          | Authentification |
|---------|-----------------------|---------------------------------------|-------------------|
| GET     | `/api/health`          | Vérifie que l'application répond      | Non               |
| GET     | `/api/tickets`         | Liste les tickets (filtrable)         | Oui               |
| GET     | `/api/tickets/<id>`    | Détail d'un ticket                    | Oui               |
| POST    | `/api/tickets`         | Crée un ticket                        | Oui               |
| PUT     | `/api/tickets/<id>`    | Modifie un ticket                     | Oui               |
| DELETE  | `/api/tickets/<id>`    | Supprime un ticket                    | Oui               |

Exemple de requête :

```bash
curl http://localhost:5000/api/health
```

```json
{
  "status": "healthy"
}
```

## Structure du projet

```
opsdesk/
│
├── app/
│   ├── __init__.py       # Application factory, logging, seed
│   ├── models.py         # Modèles SQLAlchemy (User, Ticket, Comment)
│   ├── routes.py         # Vues HTML
│   ├── api.py            # API REST JSON
│   ├── auth.py           # Authentification et rôles
│   ├── database.py       # Instance SQLAlchemy partagée
│   └── config.py         # Configuration via variables d'environnement
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── tickets.html
│   ├── ticket_detail.html
│   └── ticket_form.html
│
├── static/
│   ├── css/style.css
│   └── js/app.js
│
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_tickets.py
│   └── test_auth.py
│
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── run.py
```
