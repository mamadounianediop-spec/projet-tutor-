#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blueprint API - Endpoints REST pour les données
"""

from flask import Blueprint, jsonify, request
import sqlite3
import json

api_bp = Blueprint('api', __name__)

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

@api_bp.route('/etablissements')
def api_etablissements():
    """API pour lister les établissements avec filtres"""
    
    # Paramètres de filtrage
    type_etablissement = request.args.get('type')
    commune_id = request.args.get('commune_id')
    statut = request.args.get('statut')
    search = request.args.get('search', '').strip()
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    # Construction de la requête
    query = """
        SELECT 
            e.*,
            c.nom as commune_nom,
            c.arrondissement,
            (SELECT COUNT(*) FROM personnel p WHERE p.etablissement_id = e.id) as nombre_personnel
        FROM etablissements e
        LEFT JOIN communes c ON e.commune_id = c.id
        WHERE 1=1
    """
    
    params = []
    
    if type_etablissement:
        query += " AND e.type_etablissement = ?"
        params.append(type_etablissement)
    
    if commune_id:
        query += " AND e.commune_id = ?"
        params.append(commune_id)
    
    if statut:
        query += " AND e.statut LIKE ?"
        params.append(f'%{statut}%')
    
    if search:
        query += " AND (e.nom LIKE ? OR e.directeur LIKE ? OR c.nom LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    # Compter le total
    count_query = f"SELECT COUNT(*) as total FROM ({query}) as subq"
    total = execute_query_single(count_query, params)['total']
    
    # Ajouter pagination
    query += " ORDER BY e.nom LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    etablissements = execute_query(query, params)
    
    return jsonify({
        'etablissements': etablissements,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })

@api_bp.route('/personnel')
def api_personnel():
    """API pour lister le personnel avec filtres"""
    
    # Paramètres de filtrage
    etablissement_id = request.args.get('etablissement_id')
    corps = request.args.get('corps')
    grade = request.args.get('grade')
    fonction = request.args.get('fonction')
    genre = request.args.get('genre')
    search = request.args.get('search', '').strip()
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    offset = (page - 1) * per_page
    
    # Construction de la requête
    query = """
        SELECT 
            p.*,
            e.nom as etablissement_nom,
            e.type_etablissement,
            c.nom as commune_nom
        FROM personnel p
        LEFT JOIN etablissements e ON p.etablissement_id = e.id
        LEFT JOIN communes c ON e.commune_id = c.id
        WHERE 1=1
    """
    
    params = []
    
    if etablissement_id:
        query += " AND p.etablissement_id = ?"
        params.append(etablissement_id)
    
    if corps:
        query += " AND p.corps = ?"
        params.append(corps)
    
    if grade:
        query += " AND p.grade = ?"
        params.append(grade)
    
    if fonction:
        query += " AND p.fonction = ?"
        params.append(fonction)
    
    if genre:
        query += " AND p.genre = ?"
        params.append(genre)
    
    if search:
        query += " AND (p.nom LIKE ? OR p.prenom LIKE ? OR p.matricule LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    # Compter le total
    count_query = f"SELECT COUNT(*) as total FROM ({query}) as subq"
    total = execute_query_single(count_query, params)['total']
    
    # Ajouter pagination
    query += " ORDER BY p.nom, p.prenom LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    personnel = execute_query(query, params)
    
    return jsonify({
        'personnel': personnel,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })

@api_bp.route('/communes')
def api_communes():
    """API pour lister les communes"""
    communes = execute_query("""
        SELECT 
            c.*,
            COUNT(e.id) as nombre_etablissements
        FROM communes c
        LEFT JOIN etablissements e ON c.id = e.commune_id
        GROUP BY c.id, c.nom
        ORDER BY c.nom
    """)
    
    return jsonify({'communes': communes})

@api_bp.route('/filters/etablissements')
def api_filters_etablissements():
    """API pour les options de filtrage des établissements"""
    
    # Types d'établissements
    types = execute_query("""
        SELECT DISTINCT type_etablissement
        FROM etablissements
        WHERE type_etablissement IS NOT NULL
        ORDER BY type_etablissement
    """)
    
    # Statuts
    statuts = execute_query("""
        SELECT DISTINCT statut
        FROM etablissements
        WHERE statut IS NOT NULL
        ORDER BY statut
    """)
    
    # Communes
    communes = execute_query("""
        SELECT id, nom
        FROM communes
        ORDER BY nom
    """)
    
    return jsonify({
        'types': [t['type_etablissement'] for t in types],
        'statuts': [s['statut'] for s in statuts],
        'communes': communes
    })

@api_bp.route('/filters/personnel')
def api_filters_personnel():
    """API pour les options de filtrage du personnel"""
    
    # Corps
    corps = execute_query("""
        SELECT DISTINCT corps
        FROM personnel
        WHERE corps IS NOT NULL AND corps != ''
        ORDER BY corps
    """)
    
    # Grades
    grades = execute_query("""
        SELECT DISTINCT grade
        FROM personnel
        WHERE grade IS NOT NULL AND grade != ''
        ORDER BY grade
    """)
    
    # Fonctions
    fonctions = execute_query("""
        SELECT DISTINCT fonction
        FROM personnel
        WHERE fonction IS NOT NULL AND fonction != ''
        ORDER BY fonction
    """)
    
    # Genres
    genres = execute_query("""
        SELECT DISTINCT genre
        FROM personnel
        WHERE genre IS NOT NULL AND genre != ''
        ORDER BY genre
    """)
    
    return jsonify({
        'corps': [c['corps'] for c in corps],
        'grades': [g['grade'] for g in grades],
        'fonctions': [f['fonction'] for f in fonctions],
        'genres': [g['genre'] for g in genres]
    })

@api_bp.route('/etablissement/<int:etablissement_id>')
def api_etablissement_detail(etablissement_id):
    """Détails d'un établissement"""
    
    # Informations de l'établissement
    etablissement = execute_query_single("""
        SELECT 
            e.*,
            c.nom as commune_nom,
            c.arrondissement
        FROM etablissements e
        LEFT JOIN communes c ON e.commune_id = c.id
        WHERE e.id = ?
    """, [etablissement_id])
    
    if not etablissement:
        return jsonify({'error': 'Établissement non trouvé'}), 404
    
    # Personnel de l'établissement
    personnel = execute_query("""
        SELECT *
        FROM personnel
        WHERE etablissement_id = ?
        ORDER BY nom, prenom
    """, [etablissement_id])
    
    # Statistiques du personnel
    stats_personnel = execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN genre = 'M' OR genre = 'H' THEN 1 END) as hommes,
            COUNT(CASE WHEN genre = 'F' THEN 1 END) as femmes
        FROM personnel
        WHERE etablissement_id = ?
    """, [etablissement_id])
    
    return jsonify({
        'etablissement': etablissement,
        'personnel': personnel,
        'stats_personnel': stats_personnel
    })

@api_bp.route('/personnel/<int:personnel_id>')
def api_personnel_detail(personnel_id):
    """Détails d'une personne"""
    
    personne = execute_query_single("""
        SELECT 
            p.*,
            e.nom as etablissement_nom,
            e.type_etablissement,
            c.nom as commune_nom
        FROM personnel p
        LEFT JOIN etablissements e ON p.etablissement_id = e.id
        LEFT JOIN communes c ON e.commune_id = c.id
        WHERE p.id = ?
    """, [personnel_id])
    
    if not personne:
        return jsonify({'error': 'Personnel non trouvé'}), 404
    
    return jsonify({'personne': personne})

@api_bp.route('/export/etablissements')
def api_export_etablissements():
    """Export des données d'établissements (CSV)"""
    # TODO: Implémenter l'export CSV
    return jsonify({'message': 'Export CSV à implémenter'})

@api_bp.route('/export/personnel')
def api_export_personnel():
    """Export des données de personnel (CSV)"""
    # TODO: Implémenter l'export CSV
    return jsonify({'message': 'Export CSV à implémenter'})
