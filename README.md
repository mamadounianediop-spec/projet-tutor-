# 🎓 Système de Gestion IEF Louga

Plateforme de visualisation et de gestion des données massives de l'Inspection de l'Éducation et de la Formation (IEF) de Louga.

## 📋 Description

Ce système permet la gestion et l'analyse des données des établissements scolaires et du personnel éducatif de la région de Louga au Sénégal. Il offre une interface web moderne pour visualiser, analyser et générer des rapports sur les données de l'éducation.

## ✨ Fonctionnalités

### 🏫 Gestion des Établissements
- Visualisation de tous les établissements par type et statut
- Répartition géographique par commune et arrondissement
- Filtrage et recherche avancée
- Analyses détaillées et métriques

### 👥 Gestion du Personnel
- Suivi complet du personnel éducatif
- Répartition par corps, grade et fonction
- Gestion des affectations
- Analyses de qualification et ancienneté

### 📊 Tableau de Bord
- Vue d'ensemble des métriques clés
- Graphiques interactifs
- Indicateurs de performance
- Visualisations en temps réel

### 📈 Rapports et Analyses
- Rapport de synthèse générale
- Analyses détaillées par secteur
- Couverture territoriale
- Indicateurs de performance
- Export Excel et PDF

## 🛠️ Technologies

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Base de données**: SQLite
- **UI Framework**: Tailwind CSS
- **Graphiques**: Chart.js
- **Icons**: Font Awesome

## 📦 Installation

### Prérequis
- Python 3.8+
- pip (gestionnaire de packages Python)

### Installation
1. Cloner le repository
```bash
git clone https://github.com/mamadounianediop-spec/projet-tutor-.git
cd projet-tutor-
```

2. Créer un environnement virtuel
```bash
python -m venv .venv
```

3. Activer l'environnement virtuel
```bash
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

4. Installer les dépendances
```bash
pip install flask flask-cors
```

5. Lancer l'application
```bash
python run.py
```

6. Ouvrir votre navigateur à l'adresse : http://localhost:5000

## 📁 Structure du Projet

```
projet-tutor-/
├── app/
│   ├── __init__.py
│   ├── blueprints/
│   │   ├── main.py          # Dashboard principal
│   │   ├── etablissements.py # Gestion établissements
│   │   ├── personnel.py     # Gestion personnel
│   │   └── rapports.py      # Système de rapports
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard/
│   │   ├── etablissements/
│   │   ├── personnel/
│   │   └── rapports/
│   └── static/
│       ├── css/
│       └── js/
├── bd/                      # Données sources CSV
├── ief_louga.db            # Base de données SQLite
├── run.py                  # Point d'entrée de l'application
└── README.md
```

## 📊 Données

Le système gère les données de :
- **769 établissements** (publics, privés, communautaires)
- **2,882 membres du personnel** éducatif
- **34 communes** de la région de Louga
- **Types d'établissements** : écoles primaires, collèges, lycées, etc.

## 🚀 Fonctionnalités Avancées

### Analyses Statistiques
- Calculs automatiques des métriques clés
- Analyses de tendances
- Comparaisons sectorielles
- Indicateurs de performance

### Système de Rapports
- Génération automatique de rapports
- Export en format Excel (CSV)
- Rapports HTML imprimables
- Analyses personnalisées

### Interface Utilisateur
- Design responsive moderne
- Navigation intuitive
- Graphiques interactifs
- Recherche et filtrage en temps réel

## 👨‍💻 Auteurs

- **Mamadou Niane Diop** - Développeur principal

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📞 Support

Pour toute question ou support, contactez : [mamadounianediop.spec@gmail.com]

## 🏆 Statut du Projet

🟢 **Actif** - Le projet est activement maintenu et développé.

---

**Système de Gestion IEF Louga** - Digitalisation de l'éducation au Sénégal 🇸🇳
