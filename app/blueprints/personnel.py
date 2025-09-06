#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blueprint Personnel - Gestion et visualisation du personnel
"""

from flask import Blueprint, render_template, request, jsonify, send_file, make_response
import sqlite3
import csv
import io
from datetime import datetime

personnel_bp = Blueprint('personnel', __name__)

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

@personnel_bp.route('/')
def index():
    """Page principale du personnel"""
    
    # Statistiques générales
    stats = get_personnel_stats()
    
    # Paramètres de filtrage et pagination
    search = request.args.get('search', '').strip()
    corps_filter = request.args.get('corps', '')
    grade_filter = request.args.get('grade', '')
    genre_filter = request.args.get('genre', '')
    etablissement_filter = request.args.get('etablissement_id', '')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    # Construction de la requête pour le personnel
    personnel_query = """
        SELECT 
            p.*,
            e.nom as etablissement_nom,
            e.type_etablissement,
            c.nom as commune_nom
        FROM personnel p
        LEFT JOIN etablissements e ON p.etablissement_id = e.id
        LEFT JOIN communes c ON e.commune_id = c.id
    """
    
    # Requête pour le comptage total
    count_query = """
        SELECT COUNT(*) as total
        FROM personnel p
        LEFT JOIN etablissements e ON p.etablissement_id = e.id
        LEFT JOIN communes c ON e.commune_id = c.id
    """
    
    conditions = []
    params = []
    
    if search:
        conditions.append("(p.nom LIKE ? OR p.prenom LIKE ? OR p.matricule LIKE ?)")
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    if corps_filter:
        conditions.append("p.corps = ?")
        params.append(corps_filter)
    
    if grade_filter:
        conditions.append("p.grade = ?")
        params.append(grade_filter)
    
    if genre_filter:
        conditions.append("p.genre = ?")
        params.append(genre_filter)
    
    if etablissement_filter:
        conditions.append("p.etablissement_id = ?")
        params.append(etablissement_filter)
    
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        personnel_query += where_clause
        count_query += where_clause
    
    # Compter le total
    total_count = execute_query_single(count_query, params)['total']
    
    # Ajouter pagination
    personnel_query += " ORDER BY p.nom, p.prenom LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    personnel = execute_query(personnel_query, params)
    
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
    
    # Créer l'objet repartition_personnel pour le template
    repartition_personnel = {
        'par_corps': stats['par_corps'],
        'par_grade': stats['par_grade'],
        'par_fonction': stats['par_fonction']
    }
    
    # Données pour les filtres
    corps_list = execute_query("""
        SELECT DISTINCT corps
        FROM personnel
        WHERE corps IS NOT NULL AND corps != ''
        ORDER BY corps
    """)
    
    grades_list = execute_query("""
        SELECT DISTINCT grade
        FROM personnel
        WHERE grade IS NOT NULL AND grade != ''
        ORDER BY grade
    """)
    
    etablissements_list = execute_query("""
        SELECT id, nom
        FROM etablissements
        ORDER BY nom
    """)
    
    return render_template('personnel/index.html',
                         stats=stats,
                         personnel=personnel,
                         repartition_personnel=repartition_personnel,
                         corps_list=corps_list,
                         grades_list=grades_list,
                         etablissements_list=etablissements_list,
                         pagination=pagination,
                         filters={
                             'search': search,
                             'corps': corps_filter,
                             'grade': grade_filter,
                             'genre': genre_filter,
                             'etablissement_id': etablissement_filter
                         })

@personnel_bp.route('/corps/<corps>')
def par_corps(corps):
    """Personnel par corps"""
    
    personnel = execute_query("""
        SELECT 
            p.*,
            e.nom as etablissement_nom,
            c.nom as commune_nom
        FROM personnel p
        LEFT JOIN etablissements e ON p.etablissement_id = e.id
        LEFT JOIN communes c ON e.commune_id = c.id
        WHERE p.corps = ?
        ORDER BY p.nom, p.prenom
    """, [corps])
    
    # Statistiques du corps
    stats = execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN genre IN ('M', 'H') THEN 1 END) as hommes,
            COUNT(CASE WHEN genre = 'F' THEN 1 END) as femmes,
            COUNT(CASE WHEN etablissement_id IS NOT NULL THEN 1 END) as affectes,
            COUNT(DISTINCT grade) as nombre_grades
        FROM personnel
        WHERE corps = ?
    """, [corps])
    
    # Répartition par grade
    par_grade = execute_query("""
        SELECT 
            grade,
            COUNT(*) as count
        FROM personnel
        WHERE corps = ? AND grade IS NOT NULL
        GROUP BY grade
        ORDER BY count DESC
    """, [corps])
    
    return render_template('personnel/par_corps.html',
                         corps=corps,
                         personnel=personnel,
                         stats=stats,
                         par_grade=par_grade)

@personnel_bp.route('/non-affectes')
def non_affectes():
    """Personnel non affecté"""
    
    personnel = execute_query("""
        SELECT *
        FROM personnel
        WHERE etablissement_id IS NULL AND (service IS NULL OR service = '')
        ORDER BY nom, prenom
    """)
    
    # Statistiques
    stats = execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN genre IN ('M', 'H') THEN 1 END) as hommes,
            COUNT(CASE WHEN genre = 'F' THEN 1 END) as femmes,
            COUNT(DISTINCT corps) as nombre_corps,
            COUNT(DISTINCT grade) as nombre_grades
        FROM personnel
        WHERE etablissement_id IS NULL AND (service IS NULL OR service = '')
    """)
    
    return render_template('personnel/non_affectes.html',
                         personnel=personnel,
                         stats=stats)

@personnel_bp.route('/ief')
def ief():
    """Personnel de l'IEF (services centraux)"""
    
    personnel = execute_query("""
        SELECT *
        FROM personnel
        WHERE service IS NOT NULL AND service != ''
        ORDER BY fonction, nom, prenom
    """)
    
    # Statistiques
    stats = execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN genre IN ('M', 'H') THEN 1 END) as hommes,
            COUNT(CASE WHEN genre = 'F' THEN 1 END) as femmes,
            COUNT(DISTINCT fonction) as nombre_fonctions
        FROM personnel
        WHERE service IS NOT NULL AND service != ''
    """)
    
    # Par fonction
    par_fonction = execute_query("""
        SELECT 
            fonction,
            COUNT(*) as count
        FROM personnel
        WHERE service IS NOT NULL AND service != '' AND fonction IS NOT NULL
        GROUP BY fonction
        ORDER BY count DESC
    """)
    
    return render_template('personnel/ief.html',
                         personnel=personnel,
                         stats=stats,
                         par_fonction=par_fonction)

@personnel_bp.route('/recherche')
def recherche():
    """Page de recherche avancée"""
    
    # Options de filtres
    corps_list = execute_query("SELECT DISTINCT corps FROM personnel WHERE corps IS NOT NULL ORDER BY corps")
    grades_list = execute_query("SELECT DISTINCT grade FROM personnel WHERE grade IS NOT NULL ORDER BY grade")
    fonctions_list = execute_query("SELECT DISTINCT fonction FROM personnel WHERE fonction IS NOT NULL ORDER BY fonction")
    etablissements_list = execute_query("SELECT id, nom FROM etablissements ORDER BY nom")
    
    return render_template('personnel/recherche.html',
                         corps_list=[c['corps'] for c in corps_list],
                         grades_list=[g['grade'] for g in grades_list],
                         fonctions_list=[f['fonction'] for f in fonctions_list],
                         etablissements_list=etablissements_list)

def get_personnel_stats():
    """Statistiques générales du personnel"""
    
    # Totaux généraux
    totaux = execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN genre IN ('M', 'H') THEN 1 END) as hommes,
            COUNT(CASE WHEN genre = 'F' THEN 1 END) as femmes,
            COUNT(CASE WHEN etablissement_id IS NOT NULL THEN 1 END) as affectes_etablissement,
            COUNT(CASE WHEN service IS NOT NULL AND service != '' THEN 1 END) as affectes_service,
            COUNT(CASE WHEN etablissement_id IS NULL AND (service IS NULL OR service = '') THEN 1 END) as non_affectes
        FROM personnel
    """)
    
    # Par corps (top 8)
    par_corps = execute_query("""
        SELECT 
            corps,
            COUNT(*) as count,
            COUNT(CASE WHEN genre IN ('M', 'H') THEN 1 END) as hommes,
            COUNT(CASE WHEN genre = 'F' THEN 1 END) as femmes
        FROM personnel
        WHERE corps IS NOT NULL AND corps != ''
        GROUP BY corps
        ORDER BY count DESC
        LIMIT 8
    """)
    
    # Par grade (top 10)
    par_grade = execute_query("""
        SELECT 
            grade,
            COUNT(*) as count
        FROM personnel
        WHERE grade IS NOT NULL AND grade != ''
        GROUP BY grade
        ORDER BY count DESC
        LIMIT 10
    """)
    
    # Par fonction (top 8)
    par_fonction = execute_query("""
        SELECT 
            fonction,
            COUNT(*) as count
        FROM personnel
        WHERE fonction IS NOT NULL AND fonction != ''
        GROUP BY fonction
        ORDER BY count DESC
        LIMIT 8
    """)
    
    # Calcul des affectés
    personnel_affecte = totaux['affectes_etablissement'] + totaux['affectes_service']
    
    return {
        'total_personnel': totaux['total'],
        'personnel_hommes': totaux['hommes'],
        'personnel_femmes': totaux['femmes'],
        'personnel_affecte': personnel_affecte,
        'personnel_non_affecte': totaux['non_affectes'],
        'par_corps': par_corps,
        'par_grade': par_grade,
        'par_fonction': par_fonction
    }

# Routes d'API et exports
@personnel_bp.route('/api/export')
def api_export():
    """Export Excel du personnel avec filtres"""
    try:
        # Récupérer les mêmes filtres que la page principale
        search = request.args.get('search', '').strip()
        corps_filter = request.args.get('corps', '')
        fonction_filter = request.args.get('fonction', '')
        sexe_filter = request.args.get('sexe', '')
        statut_filter = request.args.get('statut', '')
        
        # Construction de la requête
        query = """
            SELECT 
                p.nom as 'Nom',
                p.prenom as 'Prénom',
                CASE 
                    WHEN p.genre IN ('M', 'H') THEN 'Homme'
                    WHEN p.genre = 'F' THEN 'Femme'
                    ELSE p.genre
                END as 'Genre',
                p.corps as 'Corps',
                p.grade as 'Grade',
                p.fonction as 'Fonction',
                p.diplome_academique as 'Diplôme Académique',
                p.diplome_professionnel as 'Diplôme Professionnel',
                p.service as 'Service',
                e.nom as 'Établissement',
                c.nom as 'Commune',
                p.contact as 'Contact',
                p.date_entree_enseignement as 'Date Entrée Enseignement',
                CASE 
                    WHEN p.etablissement_id IS NOT NULL THEN 'Affecté Établissement'
                    WHEN p.service IS NOT NULL AND p.service != '' THEN 'Affecté Service'
                    ELSE 'Non Affecté'
                END as 'Statut Affectation'
            FROM personnel p
            LEFT JOIN etablissements e ON p.etablissement_id = e.id
            LEFT JOIN communes c ON e.commune_id = c.id
        """
        
        conditions = []
        params = []
        
        if search:
            conditions.append("(p.nom LIKE ? OR p.prenom LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if corps_filter:
            conditions.append("p.corps = ?")
            params.append(corps_filter)
        
        if fonction_filter:
            conditions.append("p.fonction = ?")
            params.append(fonction_filter)
        
        if sexe_filter:
            if sexe_filter == 'M':
                conditions.append("p.genre IN ('M', 'H')")
            elif sexe_filter == 'F':
                conditions.append("p.genre = 'F'")
        
        if statut_filter:
            if statut_filter == 'affecte':
                conditions.append("(p.etablissement_id IS NOT NULL OR (p.service IS NOT NULL AND p.service != ''))")
            elif statut_filter == 'non_affecte':
                conditions.append("(p.etablissement_id IS NULL AND (p.service IS NULL OR p.service = ''))")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY p.nom, p.prenom"
        
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
        response.headers['Content-Disposition'] = f'attachment; filename=personnel_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'export: {str(e)}'}), 500

@personnel_bp.route('/analytics')
def analytics():
    """Page d'analyses détaillées du personnel"""
    
    # Analyses par corps
    analyses_corps = execute_query("""
        SELECT 
            corps,
            COUNT(*) as total,
            COUNT(CASE WHEN genre IN ('M', 'H') THEN 1 END) as hommes,
            COUNT(CASE WHEN genre = 'F' THEN 1 END) as femmes,
            COUNT(CASE WHEN etablissement_id IS NOT NULL THEN 1 END) as affectes_etablissement,
            COUNT(CASE WHEN service IS NOT NULL AND service != '' THEN 1 END) as affectes_service,
            COUNT(DISTINCT etablissement_id) as etablissements_differents,
            AVG(CASE WHEN date_entree_enseignement IS NOT NULL 
                THEN 2024 - CAST(SUBSTR(date_entree_enseignement, 1, 4) AS INTEGER) 
                ELSE NULL END) as anciennete_moyenne
        FROM personnel
        WHERE corps IS NOT NULL AND corps != ''
        GROUP BY corps
        ORDER BY total DESC
    """)
    
    # Analyses par fonction
    analyses_fonction = execute_query("""
        SELECT 
            fonction,
            COUNT(*) as total,
            COUNT(CASE WHEN genre IN ('M', 'H') THEN 1 END) as hommes,
            COUNT(CASE WHEN genre = 'F' THEN 1 END) as femmes,
            COUNT(CASE WHEN etablissement_id IS NOT NULL THEN 1 END) as affectes
        FROM personnel
        WHERE fonction IS NOT NULL AND fonction != ''
        GROUP BY fonction
        ORDER BY total DESC
    """)
    
    # Analyses par grade
    analyses_grade = execute_query("""
        SELECT 
            grade,
            COUNT(*) as total,
            COUNT(CASE WHEN etablissement_id IS NOT NULL THEN 1 END) as affectes,
            ROUND(COUNT(CASE WHEN etablissement_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 1) as taux_affectation
        FROM personnel
        WHERE grade IS NOT NULL AND grade != ''
        GROUP BY grade
        ORDER BY total DESC
    """)
    
    # Répartition par qualification
    qualifications = execute_query("""
        SELECT 
            diplome_academique,
            COUNT(*) as total,
            COUNT(CASE WHEN genre IN ('M', 'H') THEN 1 END) as hommes,
            COUNT(CASE WHEN genre = 'F' THEN 1 END) as femmes
        FROM personnel
        WHERE diplome_academique IS NOT NULL AND diplome_academique != ''
        GROUP BY diplome_academique
        ORDER BY total DESC
        LIMIT 15
    """)
    
    # Analyses géographiques
    repartition_geo = execute_query("""
        SELECT 
            c.arrondissement,
            COUNT(p.id) as total_personnel,
            COUNT(DISTINCT e.id) as etablissements_avec_personnel,
            COUNT(DISTINCT p.corps) as corps_differents,
            ROUND(CAST(COUNT(p.id) AS FLOAT) / NULLIF(COUNT(DISTINCT e.id), 0), 1) as personnel_par_etablissement
        FROM communes c
        LEFT JOIN etablissements e ON c.id = e.commune_id
        LEFT JOIN personnel p ON e.id = p.etablissement_id
        GROUP BY c.arrondissement
        HAVING total_personnel > 0
        ORDER BY total_personnel DESC
    """)
    
    return render_template('personnel/analytics.html',
                         analyses_corps=analyses_corps,
                         analyses_fonction=analyses_fonction,
                         analyses_grade=analyses_grade,
                         qualifications=qualifications,
                         repartition_geo=repartition_geo)

@personnel_bp.route('/<int:agent_id>')
def detail(agent_id):
    """Vue détaillée d'un agent"""
    
    # Informations de l'agent
    agent = execute_query_single("""
        SELECT 
            p.*,
            e.nom as etablissement_nom,
            e.type_etablissement,
            c.nom as commune_nom,
            c.arrondissement
        FROM personnel p
        LEFT JOIN etablissements e ON p.etablissement_id = e.id
        LEFT JOIN communes c ON e.commune_id = c.id
        WHERE p.id = ?
    """, [agent_id])
    
    if not agent:
        return render_template('errors/404.html'), 404
    
    return render_template('personnel/detail.html', agent=agent)

@personnel_bp.route('/<int:agent_id>/edit')
def edit(agent_id):
    """Page d'édition d'un agent"""
    
    # Informations de l'agent
    agent = execute_query_single("""
        SELECT * FROM personnel WHERE id = ?
    """, [agent_id])
    
    if not agent:
        return render_template('errors/404.html'), 404
    
    # Données pour les formulaires
    etablissements = execute_query("""
        SELECT id, nom FROM etablissements ORDER BY nom
    """)
    
    corps_liste = execute_query("""
        SELECT DISTINCT corps FROM personnel WHERE corps IS NOT NULL ORDER BY corps
    """)
    
    grades_liste = execute_query("""
        SELECT DISTINCT grade FROM personnel WHERE grade IS NOT NULL ORDER BY grade
    """)
    
    fonctions_liste = execute_query("""
        SELECT DISTINCT fonction FROM personnel WHERE fonction IS NOT NULL ORDER BY fonction
    """)
    
    return render_template('personnel/edit.html',
                         agent=agent,
                         etablissements=etablissements,
                         corps_liste=corps_liste,
                         grades_liste=grades_liste,
                         fonctions_liste=fonctions_liste)

@personnel_bp.route('/<int:agent_id>/fiche')
def fiche(agent_id):
    """Fiche détaillée d'un agent pour impression"""
    
    # Informations de l'agent
    agent = execute_query_single("""
        SELECT 
            p.*,
            e.nom as etablissement_nom,
            e.type_etablissement,
            e.statut as etablissement_statut,
            c.nom as commune_nom,
            c.arrondissement
        FROM personnel p
        LEFT JOIN etablissements e ON p.etablissement_id = e.id
        LEFT JOIN communes c ON e.commune_id = c.id
        WHERE p.id = ?
    """, [agent_id])
    
    if not agent:
        return render_template('errors/404.html'), 404
    
    return render_template('personnel/fiche.html', agent=agent)
