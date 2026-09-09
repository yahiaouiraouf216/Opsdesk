# OpsDesk

OpsDesk est une application interne de gestion de tickets de support IT, conçue pour une petite équipe technique.

Les utilisateurs peuvent soumettre des demandes (matériel, réseau, accès, sécurité, etc.) et les techniciens peuvent les prendre en charge, les prioriser et suivre leur résolution.

Le projet a également été utilisé comme **projet DevOps de bout en bout**, avec conteneurisation Docker, CI avec GitHub Actions, Infrastructure as Code avec Terraform et déploiement sur AWS EC2.

---

## Fonctionnalités

* Création, consultation, modification et suppression de tickets
* Gestion du statut (`Open`, `In Progress`, `Waiting`, `Resolved`, `Closed`)
* Gestion de la priorité (`Low`, `Medium`, `High`, `Critical`)
* Catégorisation des tickets (`Hardware`, `Software`, `Network`, `Access`, `Security`, `Other`)
* Assignation des tickets à un technicien
* Commentaires sur chaque ticket
* Recherche et filtrage (titre, statut, priorité, catégorie, technicien)
* Tableau de bord avec statistiques
* Authentification par session avec deux rôles : `user` et `technician`
* API REST JSON
* Endpoint `/api/health` pour les vérifications de disponibilité
* Logs applicatifs écrits vers `stdout/stderr`

---

# Architecture de l'application

```text
Navigateur
    │
    ▼
Flask (Blueprints)
 ├── auth.py     → authentification (login/logout, hashing, rôles)
 ├── routes.py   → vues HTML (dashboard, tickets, formulaires)
 └── api.py      → API REST JSON
    │
    ▼
SQLAlchemy
    │
    ▼
PostgreSQL
```

L'application suit une architecture en couches simple :

* **Présentation** : templates Jinja2 + Bootstrap (`templates/`, `static/`)
* **Logique applicative** : blueprints Flask (`app/routes.py`, `app/api.py`, `app/auth.py`)
* **Accès aux données** : modèles SQLAlchemy (`app/models.py`) et instance `db` partagée (`app/database.py`)
* **Configuration** : variables d'environnement (`app/config.py`)

---

# Stack technique

| Composant                    | Technologie                              |
| ---------------------------- | ---------------------------------------- |
| Langage                      | Python 3                                 |
| Framework web                | Flask                                    |
| ORM                          | SQLAlchemy / Flask-SQLAlchemy            |
| Base de données              | PostgreSQL                               |
| Frontend                     | HTML, CSS, Bootstrap 5, JavaScript léger |
| Tests                        | pytest                                   |
| Authentification             | Sessions Flask + Werkzeug                |
| Conteneurisation             | Docker                                   |
| Orchestration des conteneurs | Docker Compose                           |
| CI                           | GitHub Actions                           |
| Infrastructure as Code       | Terraform                                |
| Cloud                        | AWS                                      |
| Compute                      | Amazon EC2                               |
| Networking                   | Amazon VPC                               |
| Monitoring                   | Amazon CloudWatch                        |
| Version Control              | Git / GitHub                             |

---

# Prérequis

Pour l'installation locale sans Docker :

* Python 3.10 ou supérieur
* PostgreSQL 13 ou supérieur
* `pip`
* `venv`

Pour le déploiement conteneurisé :

* Docker
* Docker Compose

Pour l'infrastructure AWS :

* AWS CLI configuré
* Terraform
* Compte AWS

---

# Installation locale

## Installation de Python

Vérifiez que Python 3 est installé :

```bash
python3 --version
```

Si nécessaire, installez-le depuis [python.org](https://www.python.org/downloads/) ou via le gestionnaire de paquets de votre système.

---

# Installation de PostgreSQL

## macOS — Homebrew

```bash
brew install postgresql@16
brew services start postgresql@16
```

## Ubuntu / Debian

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

## Windows

Téléchargez l'installateur depuis [postgresql.org/download](https://www.postgresql.org/download/windows/).

---

# Création de la base de données

Connectez-vous à PostgreSQL :

```bash
psql -U postgres
```

Puis créez l'utilisateur et les bases de données :

```sql
CREATE USER opsdesk_user WITH PASSWORD 'change-me';
CREATE DATABASE opsdesk OWNER opsdesk_user;
CREATE DATABASE opsdesk_test OWNER opsdesk_user;
\q
```

Les tables sont créées automatiquement par l'application au premier démarrage via `db.create_all()`.

Aucune migration manuelle n'est requise pour ce projet.

---

# Configuration des variables d'environnement

Copiez le fichier d'exemple :

```bash
cp .env.example .env
```

Puis configurez vos propres valeurs :

```text
DATABASE_URL=postgresql://opsdesk_user:change-me@localhost:5432/opsdesk
SECRET_KEY=une-valeur-secrete-aleatoire
APP_ENV=development
PORT=5000
TEST_DATABASE_URL=postgresql://opsdesk_user:change-me@localhost:5432/opsdesk_test
```

⚠️ **Ne committez jamais le fichier `.env`.**

Le fichier `.env` est exclu du repository via `.gitignore`.

Le repository contient uniquement `.env.example`, qui ne contient aucune vraie information sensible.

---

# Installation des dépendances

Créez un environnement virtuel :

```bash
python3 -m venv .venv
```

Activez-le :

```bash
source .venv/bin/activate
```

Sous Windows :

```text
.venv\Scripts\activate
```

Installez les dépendances :

```bash
pip install -r requirements.txt
```

---

# Lancement de l'application

Chargez les variables d'environnement :

```bash
export $(grep -v '^#' .env | xargs)
```

Puis démarrez l'application :

```bash
python run.py
```

L'application est accessible à :

```text
http://localhost:5000
```

Au premier démarrage, des comptes et tickets de démonstration sont automatiquement créés.

| Utilisateur | Rôle       | Mot de passe |
| ----------- | ---------- | ------------ |
| alice       | user       | password123  |
| bob         | user       | password123  |
| tania.tech  | technician | password123  |
| marc.tech   | technician | password123  |

> Ces comptes sont uniquement destinés à la démonstration et au développement.

---

# Tests

Les tests utilisent une base de données séparée (`TEST_DATABASE_URL`) afin de ne pas modifier les données de développement.

Lancer les tests :

```bash
export APP_ENV=testing
pytest
```

Ou :

```bash
APP_ENV=testing pytest -v
```

---

# API REST

| Méthode | Endpoint            | Description                      | Authentification |
| ------- | ------------------- | -------------------------------- | ---------------- |
| GET     | `/api/health`       | Vérifie que l'application répond | Non              |
| GET     | `/api/tickets`      | Liste les tickets                | Oui              |
| GET     | `/api/tickets/<id>` | Détail d'un ticket               | Oui              |
| POST    | `/api/tickets`      | Crée un ticket                   | Oui              |
| PUT     | `/api/tickets/<id>` | Modifie un ticket                | Oui              |
| DELETE  | `/api/tickets/<id>` | Supprime un ticket               | Oui              |

## Health check

```bash
curl http://localhost:5000/api/health
```

Réponse attendue :

```json
{
  "status": "healthy"
}
```

---

# 🐳 Docker

OpsDesk peut être exécuté avec Docker Compose.

L'environnement contient deux services :

```text
Docker Compose
│
├── app
│   └── OpsDesk / Flask
│
└── postgres
    └── PostgreSQL
```

## Construire et démarrer les services

```bash
docker compose up -d --build
```

* `up` → démarre les services
* `-d` → exécute les conteneurs en arrière-plan
* `--build` → reconstruit l'image de l'application

## Vérifier les conteneurs

```bash
docker compose ps
```

## Afficher les logs

```bash
docker compose logs
```

Pour suivre les logs en temps réel :

```bash
docker compose logs -f
```

## Arrêter les services

```bash
docker compose down
```

L'application est accessible à :

```text
http://localhost:5000
```

---

# 🔄 CI — GitHub Actions

Le projet utilise **GitHub Actions** pour automatiser la validation du code.

Le workflow suit le principe :

```text
git push
    │
    ▼
GitHub Actions
    │
    ├── Installation des dépendances
    │
    ├── Configuration de l'environnement de test
    │
    ├── Exécution des tests pytest
    │
    └── Validation du code
```

L'objectif est de détecter les erreurs automatiquement avant de considérer une modification comme prête.

---

# ☁️ Infrastructure as Code — Terraform

L'infrastructure AWS est définie avec Terraform.

Terraform permet de créer et gérer l'infrastructure à partir de fichiers de configuration plutôt que de créer manuellement chaque ressource dans la console AWS.

## Initialiser Terraform

```bash
terraform init
```

## Vérifier le plan

```bash
terraform plan
```

## Créer l'infrastructure

```bash
terraform apply
```

Terraform provisionne notamment :

* VPC
* Subnet public
* Internet Gateway
* Route Table
* Security Group
* EC2
* SSH key configuration

---

# AWS Deployment

L'application est déployée sur une instance **Amazon EC2 Ubuntu**.

Architecture simplifiée :

```text
                        Internet
                           │
                           │ HTTP :5000
                           ▼
                  ┌──────────────────┐
                  │     AWS EC2      │
                  │     Ubuntu       │
                  │                  │
                  │ Docker Compose   │
                  │                  │
                  │ ┌──────────────┐ │
                  │ │   OpsDesk    │ │
                  │ │    Flask     │ │
                  │ │    :5000     │ │
                  │ └──────┬───────┘ │
                  │        │          │
                  │ ┌──────▼───────┐  │
                  │ │  PostgreSQL  │  │
                  │ └──────────────┘  │
                  └──────────────────┘
                           │
                           ▼
                      CloudWatch
```

Pour ce projet de portfolio, l'application et PostgreSQL sont exécutés sur la même instance EC2 afin de garder l'architecture simple et de limiter les coûts AWS.

---

# 🔐 SSH Deployment

L'instance EC2 est accessible avec une clé SSH.

Exemple :

```bash
ssh -i ~/.ssh/opsdesk-key ubuntu@<EC2_PUBLIC_IP>
```

Une fois connecté :

```bash
git clone <repository-url>
cd OpsDesk
```

Puis démarrez l'application :

```bash
sudo docker compose up -d --build
```

Vérifiez les conteneurs :

```bash
sudo docker compose ps
```

Testez l'application directement depuis l'EC2 :

```bash
curl http://localhost:5000/api/health
```

Réponse attendue :

```json
{
  "status": "healthy"
}
```

L'application peut ensuite être ouverte depuis un navigateur :

```text
http://<EC2_PUBLIC_IP>:5000
```

---

# 📊 Monitoring — Amazon CloudWatch

Les métriques de base de l'instance EC2 sont disponibles dans **Amazon CloudWatch**.

Elles permettent notamment de suivre :

* CPU utilization
* Network traffic
* EC2 status checks
* EBS metrics

Les logs de l'application peuvent également être consultés avec Docker :

```bash
sudo docker compose logs
```

---

# 🔒 Security

Les pratiques de sécurité suivantes sont appliquées dans le projet :

* Les secrets ne sont pas commités dans Git.
* `.env` est exclu avec `.gitignore`.
* `.env.example` contient uniquement des valeurs d'exemple.
* L'accès à EC2 utilise une clé SSH.
* PostgreSQL n'est pas directement exposé à Internet.
* L'infrastructure AWS est gérée avec Terraform.

### Évolutions possibles pour une architecture production

Pour un environnement réellement production, l'architecture pourrait être améliorée avec :

* HTTPS / TLS
* Application Load Balancer
* RDS PostgreSQL
* Private Subnets
* AWS Secrets Manager
* AWS Systems Manager Session Manager
* IAM least privilege
* Centralisation des logs
* Container Registry
* Déploiement CI/CD automatisé vers AWS

---

# 💰 AWS Cost Management

L'infrastructure AWS de ce projet est destinée à l'apprentissage et au portfolio.

Les ressources doivent être supprimées lorsqu'elles ne sont plus nécessaires afin d'éviter les coûts inutiles.

Depuis le dossier Terraform :

```bash
terraform destroy
```

Terraform affichera les ressources qui seront supprimées et demandera une confirmation.

---

# 📁 Structure du projet

```text
opsdesk/
│
├── app/
│   ├── __init__.py       # Application factory, logging, seed
│   ├── models.py         # Modèles SQLAlchemy
│   ├── routes.py         # Vues HTML
│   ├── api.py            # API REST JSON
│   ├── auth.py           # Authentification et rôles
│   ├── database.py       # Instance SQLAlchemy
│   └── config.py         # Configuration
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
├── terraform/
│   ├── main.tf
│   ├── data.tf
│   ├── outputs.tf
│   └── ...
│
├── .github/
│   └── workflows/
│       └── ...
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── run.py
```

---

# 🧑‍💻 DevOps Workflow

Le projet couvre le cycle complet suivant :

```text
                Code
                 │
                 ▼
             Git / GitHub
                 │
                 ▼
          GitHub Actions
                 │
                 ▼
               Tests
                 │
                 ▼
              Docker
                 │
                 ▼
             Terraform
                 │
                 ▼
               AWS
                 │
                 ▼
              EC2
                 │
                 ▼
          Docker Compose
                 │
          ┌──────┴──────┐
          ▼             ▼
       OpsDesk       PostgreSQL
          │
          ▼
       Monitoring
       CloudWatch
```

---

# 🎯 DevOps Skills Demonstrated

Ce projet démontre une expérience pratique avec :

* Linux
* Git / GitHub
* GitHub Actions
* CI
* Docker
* Docker Compose
* PostgreSQL
* Terraform
* Infrastructure as Code
* AWS EC2
* AWS VPC
* Security Groups
* SSH
* CloudWatch
* Environment variables
* Secrets management
* Containerization
* Cloud deployment
* Troubleshooting
* Cost management

---

# 💼 Project Summary

**OpsDesk — End-to-End DevOps Project**

Built and deployed a containerized Flask/PostgreSQL IT ticket management application using Docker Compose, GitHub Actions, Terraform and AWS EC2.

Provisioned AWS infrastructure using Infrastructure as Code, implemented automated testing with GitHub Actions, deployed the application to a Linux server using Docker Compose, and used CloudWatch for infrastructure monitoring.

### Technologies

`AWS` · `Terraform` · `Docker` · `Docker Compose` · `GitHub Actions` · `Linux` · `Python` · `Flask` · `PostgreSQL` · `Git`
