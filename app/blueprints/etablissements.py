#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blueprint Établissements - Gestion et visualisation des établissements
"""

from flask import Blueprint, render_template, request, jsonify, send_file, make_response
import sqlite3
import csv
import io
from datetime import datetime

etablissements_bp = Blueprint('etablissements', __name__)

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

@etablissements_bp.route('/')
def index():
    """Page principale des établissements"""
    
    # Statistiques générales
    stats = get_etablissements_stats()
    
    # Paramètres de filtrage et pagination
    search = request.args.get('search', '').strip()
    type_filter = request.args.get('type_etablissement', '')
    commune_filter = request.args.get('commune_id', '')
    statut_filter = request.args.get('statut', '')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    # Construction de la requête pour les établissements
    etablissements_query = """
        SELECT 
            e.*,
            c.nom as commune_nom,
            COUNT(p.id) as personnel_count
        FROM etablissements e
        LEFT JOIN communes c ON e.commune_id = c.id
        LEFT JOIN personnel p ON e.id = p.etablissement_id
    """
    
    # Requête pour le comptage total
    count_query = """
        SELECT COUNT(DISTINCT e.id) as total
        FROM etablissements e
        LEFT JOIN communes c ON e.commune_id = c.id
    """
    
    conditions = []
    params = []
    
    if search:
        conditions.append("(e.nom LIKE ? OR e.code LIKE ?)")
        params.extend([f'%{search}%', f'%{search}%'])
    
    if type_filter:
        conditions.append("e.type_etablissement = ?")
        params.append(type_filter)
    
    if commune_filter:
        conditions.append("e.commune_id = ?")
        params.append(commune_filter)
    
    if statut_filter:
        conditions.append("e.statut LIKE ?")
        params.append(f'%{statut_filter}%')
    
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        etablissements_query += where_clause
        count_query += where_clause
    
    # Compter le total
    total_count = execute_query_single(count_query, params)['total']
    
    # Ajouter pagination et groupement
    etablissements_query += " GROUP BY e.id ORDER BY e.nom LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    etablissements = execute_query(etablissements_query, params)
    
    # Calculs de pagination
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    # Génération des numéros de pages
    def iter_pages(left_edge=2, left_current=2, right_current=3, right_edge=2):
        last = total_pages
        for num in range(1, last + 1):
            if num <= left_edge or \
               (page - left_current - 1 < num < page + right_current) or \
               num > last - right_edge:
                yield num
            elif num == page - left_current - 1 or num == page + right_current:
                yield None
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_count,
        'total_pages': total_pages,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_num': page - 1 if has_prev else None,
        'next_num': page + 1 if has_next else None,
        'iter_pages': lambda: iter_pages()
    }
    
    # Données pour les filtres
    types_etablissements = execute_query("""
        SELECT DISTINCT type_etablissement
        FROM etablissements
        WHERE type_etablissement IS NOT NULL
        ORDER BY type_etablissement
    """)
    
    communes_list = execute_query("""
        SELECT id, nom
        FROM communes
        ORDER BY nom
    """)
    
    return render_template('etablissements/index.html',
                         stats=stats,
                         etablissements=etablissements,
                         types_etablissements=types_etablissements,
                         communes_list=communes_list,
                         pagination=pagination,
                         filters={
                             'search': search,
                             'type_etablissement': type_filter,
                             'commune_id': commune_filter,
                             'statut': statut_filter
                         })

@etablissements_bp.route('/carte')
def carte():
    """Carte géographique des établissements"""
    
    # Établissements avec coordonnées
    etablissements_geo = execute_query("""
        SELECT 
            e.*,
            c.nom as commune_nom
        FROM etablissements e
        LEFT JOIN communes c ON e.commune_id = c.id
        WHERE e.coordonnees_x IS NOT NULL AND e.coordonnees_y IS NOT NULL
    """)
    
    return render_template('etablissements/carte.html',
                         etablissements=etablissements_geo)

@etablissements_bp.route('/detail/<int:etablissement_id>')
def detail(etablissement_id):
    """Détail d'un établissement"""
    
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
        return render_template('errors/404.html'), 404
    
    # Personnel de l'établissement
    personnel = execute_query("""
        SELECT *
        FROM personnel
        WHERE etablissement_id = ?
        ORDER BY nom, prenom
    """, [etablissement_id])
    
    # Statistiques du personnel
    stats_personnel = get_etablissement_personnel_stats(etablissement_id)
    
    return render_template('etablissements/detail.html',
                         etablissement=etablissement,
                         personnel=personnel,
                         stats_personnel=stats_personnel)

@etablissements_bp.route('/type/<type_etablissement>')
def par_type(type_etablissement):
    """Établissements par type"""
    
    etablissements = execute_query("""
        SELECT 
            e.*,
            c.nom as commune_nom,
            (SELECT COUNT(*) FROM personnel p WHERE p.etablissement_id = e.id) as nombre_personnel
        FROM etablissements e
        LEFT JOIN communes c ON e.commune_id = c.id
        WHERE e.type_etablissement = ?
        ORDER BY e.nom
    """, [type_etablissement])
    
    # Statistiques du type
    stats = execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN statut LIKE '%Public%' THEN 1 END) as publics,
            COUNT(CASE WHEN statut LIKE '%Privé%' THEN 1 END) as prives,
            COUNT(CASE WHEN coordonnees_x IS NOT NULL THEN 1 END) as avec_coordonnees
        FROM etablissements
        WHERE type_etablissement = ?
    """, [type_etablissement])
    
    return render_template('etablissements/par_type.html',
                         type_etablissement=type_etablissement,
                         etablissements=etablissements,
                         stats=stats)

def get_etablissements_stats():
    """Statistiques générales des établissements"""
    
    # Total établissements
    total_etablissements = execute_query_single(
        "SELECT COUNT(*) as count FROM etablissements"
    )['count']
    
    # Total communes
    total_communes = execute_query_single(
        "SELECT COUNT(*) as count FROM communes"
    )['count']
    
    # Établissements par statut
    etablissements_publics = execute_query_single(
        "SELECT COUNT(*) as count FROM etablissements WHERE statut LIKE '%Public%'"
    )['count']
    
    etablissements_prives = execute_query_single(
        "SELECT COUNT(*) as count FROM etablissements WHERE statut LIKE '%Privé%' OR statut LIKE '%privé%'"
    )['count']
    
    etablissements_com_ass = execute_query_single(
        "SELECT COUNT(*) as count FROM etablissements WHERE statut LIKE '%Com_Ass%'"
    )['count']
    
    # Totaux par type
    par_type = execute_query("""
        SELECT 
            type_etablissement,
            COUNT(*) as count,
            COUNT(CASE WHEN statut LIKE '%Public%' THEN 1 END) as publics,
            COUNT(CASE WHEN statut LIKE '%Privé%' THEN 1 END) as prives
        FROM etablissements
        GROUP BY type_etablissement
        ORDER BY count DESC
    """)
    
    # Par commune (top 10)
    par_commune = execute_query("""
        SELECT 
            c.nom as commune,
            COUNT(e.id) as count
        FROM communes c
        LEFT JOIN etablissements e ON c.id = e.commune_id
        GROUP BY c.id, c.nom
        HAVING count > 0
        ORDER BY count DESC
        LIMIT 10
    """)
    
    # Géolocalisation
    geo_stats = execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN coordonnees_x IS NOT NULL THEN 1 END) as avec_coordonnees,
            COUNT(CASE WHEN directeur IS NOT NULL AND directeur != '' THEN 1 END) as avec_directeur,
            COUNT(CASE WHEN contact_1 IS NOT NULL AND contact_1 != '' THEN 1 END) as avec_contact
        FROM etablissements
    """)
    
    return {
        'total_etablissements': total_etablissements,
        'total_communes': total_communes,
        'etablissements_publics': etablissements_publics,
        'etablissements_prives': etablissements_prives,
        'etablissements_com_ass': etablissements_com_ass,
        'par_type': par_type,
        'par_commune': par_commune,
        'geo_stats': geo_stats
    }

def get_etablissement_personnel_stats(etablissement_id):
    """Statistiques du personnel d'un établissement"""
    
    return execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN genre IN ('M', 'H') THEN 1 END) as hommes,
            COUNT(CASE WHEN genre = 'F' THEN 1 END) as femmes,
            COUNT(CASE WHEN contact IS NOT NULL AND contact != '' THEN 1 END) as avec_contact,
            COUNT(DISTINCT corps) as nombre_corps,
            COUNT(DISTINCT grade) as nombre_grades,
            COUNT(DISTINCT fonction) as nombre_fonctions
        FROM personnel
        WHERE etablissement_id = ?
    """, [etablissement_id])

# Routes d'API et exports
@etablissements_bp.route('/api/export')
def api_export():
    """Export Excel des établissements avec filtres"""
    try:
        # Récupérer les mêmes filtres que la page principale
        search = request.args.get('search', '').strip()
        type_filter = request.args.get('type', '')
        commune_filter = request.args.get('commune_id', '')
        statut_filter = request.args.get('statut', '')
        
        # Construction de la requête
        query = """
            SELECT 
                e.nom as 'Nom Établissement',
                e.code_etablissement as 'Code',
                e.type_etablissement as 'Type',
                e.statut as 'Statut',
                c.nom as 'Commune',
                c.arrondissement as 'Arrondissement',
                e.directeur as 'Directeur',
                e.contact_1 as 'Contact 1',
                e.contact_2 as 'Contact 2',
                e.email_directeur as 'Email Directeur',
                e.adresse as 'Adresse',
                e.coordonnees_x as 'Longitude',
                e.coordonnees_y as 'Latitude',
                COUNT(p.id) as 'Nombre Personnel'
            FROM etablissements e
            LEFT JOIN communes c ON e.commune_id = c.id
            LEFT JOIN personnel p ON e.id = p.etablissement_id
        """
        
        conditions = []
        params = []
        
        if search:
            conditions.append("(e.nom LIKE ? OR e.code LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if type_filter:
            conditions.append("e.type_etablissement = ?")
            params.append(type_filter)
        
        if commune_filter:
            conditions.append("e.commune_id = ?")
            params.append(commune_filter)
        
        if statut_filter:
            conditions.append("e.statut LIKE ?")
            params.append(f'%{statut_filter}%')
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " GROUP BY e.id ORDER BY e.nom"
        
        # Exécuter la requête
        data = execute_query(query, params)
        
        # Créer le fichier CSV
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        # Créer la réponse
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=etablissements_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'export: {str(e)}'}), 500

@etablissements_bp.route('/analytics')
def analytics():
    """Page d'analyses détaillées des établissements"""
    
    # Analyses par type
    analyses_type = execute_query("""
        SELECT 
            type_etablissement,
            COUNT(*) as total,
            COUNT(CASE WHEN statut LIKE '%Public%' THEN 1 END) as publics,
            COUNT(CASE WHEN statut LIKE '%Privé%' THEN 1 END) as prives,
            COUNT(CASE WHEN statut LIKE '%Com_Ass%' THEN 1 END) as communautaires,
            AVG((SELECT COUNT(*) FROM personnel p WHERE p.etablissement_id = e.id)) as personnel_moyen,
            COUNT(CASE WHEN coordonnees_x IS NOT NULL THEN 1 END) as geolocalises
        FROM etablissements e
        WHERE type_etablissement IS NOT NULL
        GROUP BY type_etablissement
        ORDER BY total DESC
    """)
    
    # Analyses par commune
    analyses_commune = execute_query("""
        SELECT 
            c.nom as commune,
            c.arrondissement,
            COUNT(e.id) as total_etablissements,
            COUNT(DISTINCT e.type_etablissement) as types_differents,
            COUNT(p.id) as total_personnel,
            ROUND(CAST(COUNT(p.id) AS FLOAT) / NULLIF(COUNT(e.id), 0), 1) as ratio_personnel_etablissement
        FROM communes c
        LEFT JOIN etablissements e ON c.id = e.commune_id
        LEFT JOIN personnel p ON e.id = p.etablissement_id
        GROUP BY c.id, c.nom, c.arrondissement
        HAVING total_etablissements > 0
        ORDER BY total_etablissements DESC
    """)
    
    # Taux de géolocalisation
    geo_analyse = execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN coordonnees_x IS NOT NULL THEN 1 END) as avec_coordonnees,
            COUNT(CASE WHEN directeur IS NOT NULL AND directeur != '' THEN 1 END) as avec_directeur,
            COUNT(CASE WHEN contact_1 IS NOT NULL AND contact_1 != '' THEN 1 END) as avec_contact,
            COUNT(CASE WHEN email_directeur IS NOT NULL AND email_directeur != '' THEN 1 END) as avec_email
        FROM etablissements
    """)
    
    # Performance par type (simulation)
    performance_type = execute_query("""
        SELECT 
            type_etablissement,
            COUNT(*) as nombre,
            AVG((SELECT COUNT(*) FROM personnel p WHERE p.etablissement_id = e.id)) as personnel_moyen,
            COUNT(CASE WHEN directeur IS NOT NULL THEN 1 END) as avec_directeur,
            ROUND(COUNT(CASE WHEN directeur IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 1) as taux_encadrement
        FROM etablissements e
        WHERE type_etablissement IS NOT NULL
        GROUP BY type_etablissement
        ORDER BY personnel_moyen DESC
    """)
    
    return render_template('etablissements/analytics.html',
                         analyses_type=analyses_type,
                         analyses_commune=analyses_commune,
                         geo_analyse=geo_analyse,
                         performance_type=performance_type)

@etablissements_bp.route('/<int:etablissement_id>')
def view_detail(etablissement_id):
    """Vue détaillée d'un établissement (alias pour detail)"""
    return detail(etablissement_id)

@etablissements_bp.route('/<int:etablissement_id>/fiche')
def fiche(etablissement_id):
    """Fiche détaillée d'un établissement pour impression"""
    
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
        return render_template('errors/404.html'), 404
    
    # Personnel de l'établissement
    personnel = execute_query("""
        SELECT 
            nom, prenom, genre, corps, grade, fonction,
            diplome_academique, diplome_professionnel,
            contact, date_entree_enseignement
        FROM personnel
        WHERE etablissement_id = ?
        ORDER BY corps, grade, nom, prenom
    """, [etablissement_id])
    
    # Statistiques du personnel
    stats_personnel = execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN genre IN ('M', 'H') THEN 1 END) as hommes,
            COUNT(CASE WHEN genre = 'F' THEN 1 END) as femmes,
            COUNT(DISTINCT corps) as nombre_corps,
            COUNT(DISTINCT grade) as nombre_grades,
            COUNT(DISTINCT fonction) as nombre_fonctions
        FROM personnel
        WHERE etablissement_id = ?
    """, [etablissement_id])
    
    return render_template('etablissements/fiche.html',
                         etablissement=etablissement,
                         personnel=personnel,
                         stats_personnel=stats_personnel)
