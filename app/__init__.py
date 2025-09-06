#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Flask - Plateforme d'Analyse IEF Louga
Architecture MVC professionnelle avec design moderne
"""

from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime
import sqlite3

# Configuration de l'application
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ief-louga-secret-key-2025'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ief_louga.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# Initialisation des extensions
db = SQLAlchemy()
cors = CORS()

def create_app():
    """Factory pattern pour créer l'application Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialisation des extensions
    db.init_app(app)
    cors.init_app(app)
    
    # Enregistrement des blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.api import api_bp
    from app.blueprints.etablissements import etablissements_bp
    from app.blueprints.personnel import personnel_bp
    from app.blueprints.rapports import rapports_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(etablissements_bp, url_prefix='/etablissements')
    app.register_blueprint(personnel_bp, url_prefix='/personnel')
    app.register_blueprint(rapports_bp, url_prefix='/rapports')
    
    # Filtres personnalisés pour les templates
    @app.template_filter('format_number')
    def format_number(value):
        """Formate un nombre avec des espaces comme séparateurs de milliers"""
        if value is None:
            return "0"
        return f"{value:,}".replace(',', ' ')
    
    @app.template_filter('format_percentage')
    def format_percentage(value, total):
        """Calcule et formate un pourcentage"""
        if total == 0:
            return "0%"
        percentage = (value / total) * 100
        return f"{percentage:.1f}%"
    
    # Gestionnaire d'erreurs
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    return app

# Classes de modèles pour l'ORM (optionnel, on utilise directement SQLite)
class Commune(db.Model):
    """Modèle pour les communes"""
    __tablename__ = 'communes'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    arrondissement = db.Column(db.String(100))
    departement = db.Column(db.String(100), default='LOUGA')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    etablissements = db.relationship('Etablissement', backref='commune_obj', lazy='dynamic')

class Etablissement(db.Model):
    """Modèle pour les établissements"""
    __tablename__ = 'etablissements'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50))
    type_etablissement = db.Column(db.String(50))
    cycle = db.Column(db.String(50))
    statut = db.Column(db.String(50))
    type_statut = db.Column(db.String(100))
    commune_id = db.Column(db.Integer, db.ForeignKey('communes.id'))
    zone = db.Column(db.String(100))
    adresse = db.Column(db.Text)
    coordonnees_x = db.Column(db.Numeric(10, 2))
    coordonnees_y = db.Column(db.Numeric(10, 2))
    directeur = db.Column(db.String(200))
    contact_1 = db.Column(db.String(20))
    contact_2 = db.Column(db.String(20))
    email_directeur = db.Column(db.String(200))
    date_creation = db.Column(db.Date)
    date_ouverture = db.Column(db.Date)
    observations = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    personnel = db.relationship('Personnel', backref='etablissement_obj', lazy='dynamic')

class Personnel(db.Model):
    """Modèle pour le personnel"""
    __tablename__ = 'personnel'
    
    id = db.Column(db.Integer, primary_key=True)
    matricule = db.Column(db.String(50), unique=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(10))
    date_naissance = db.Column(db.Date)
    lieu_naissance = db.Column(db.String(200))
    numero_cni = db.Column(db.String(50))
    corps = db.Column(db.String(50))
    grade = db.Column(db.String(50))
    fonction = db.Column(db.String(100))
    specialite = db.Column(db.String(100))
    etablissement_id = db.Column(db.Integer, db.ForeignKey('etablissements.id'))
    service = db.Column(db.String(100))
    contact = db.Column(db.String(50))
    email = db.Column(db.String(200))
    diplome_academique = db.Column(db.String(100))
    diplome_professionnel = db.Column(db.String(100))
    date_entree_enseignement = db.Column(db.Date)
    date_arrivee_poste = db.Column(db.Date)
    situation_matrimoniale = db.Column(db.String(50))
    nombre_enfants = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Fonctions utilitaires pour les requêtes directes SQLite
def get_db_connection():
    """Obtient une connexion à la base de données SQLite"""
    conn = sqlite3.connect('ief_louga.db')
    conn.row_factory = sqlite3.Row  # Pour avoir des résultats sous forme de dictionnaire
    return conn

def execute_query(query, params=None):
    """Exécute une requête et retourne les résultats"""
    conn = get_db_connection()
    try:
        if params:
            cursor = conn.execute(query, params)
        else:
            cursor = conn.execute(query)
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    finally:
        conn.close()

def execute_query_single(query, params=None):
    """Exécute une requête et retourne un seul résultat"""
    conn = get_db_connection()
    try:
        if params:
            cursor = conn.execute(query, params)
        else:
            cursor = conn.execute(query)
        
        result = cursor.fetchone()
        return dict(result) if result else None
    finally:
        conn.close()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
