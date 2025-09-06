#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blueprint principal - Dashboard général et page d'accueil
"""

from flask import Blueprint, render_template, jsonify
import sqlite3
from datetime import datetime

main_bp = Blueprint('main', __name__)

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

@main_bp.route('/')
def index():
    """Page d'accueil avec dashboard principal"""
    
    # Statistiques générales
    stats = get_general_statistics()
    
    # Données pour les graphiques
    repartition_etablissements = get_etablissements_by_type()
    repartition_communes = get_etablissements_by_commune()
    repartition_personnel = get_personnel_statistics()
    
    # Date et heure actuelles
    current_time = datetime.now().strftime('%d/%m/%Y à %H:%M')
    
    return render_template('dashboard/index.html',
                         stats=stats,
                         repartition_etablissements=repartition_etablissements,
                         repartition_communes=repartition_communes,
                         repartition_personnel=repartition_personnel,
                         current_time=current_time)

@main_bp.route('/api/dashboard/stats')
def api_dashboard_stats():
    """API pour les statistiques du dashboard"""
    stats = get_general_statistics()
    return jsonify(stats)

def get_general_statistics():
    """Récupère les statistiques générales"""
    
    # Total établissements
    total_etablissements = execute_query_single(
        "SELECT COUNT(*) as count FROM etablissements"
    )['count']
    
    # Total personnel
    total_personnel = execute_query_single(
        "SELECT COUNT(*) as count FROM personnel"
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
        "SELECT COUNT(*) as count FROM etablissements WHERE statut LIKE '%Com_Ass%' OR statut LIKE '%Communautaire%'"
    )['count']
    
    # Personnel par genre
    personnel_hommes = execute_query_single(
        "SELECT COUNT(*) as count FROM personnel WHERE genre IN ('M', 'H')"
    )['count']
    
    personnel_femmes = execute_query_single(
        "SELECT COUNT(*) as count FROM personnel WHERE genre = 'F'"
    )['count']
    
    # Personnel affecté vs non affecté
    personnel_affecte = execute_query_single(
        "SELECT COUNT(*) as count FROM personnel WHERE etablissement_id IS NOT NULL OR service IS NOT NULL"
    )['count']
    
    personnel_non_affecte = total_personnel - personnel_affecte
    
    return {
        'total_etablissements': total_etablissements,
        'total_personnel': total_personnel,
        'total_communes': total_communes,
        'etablissements_publics': etablissements_publics,
        'etablissements_prives': etablissements_prives,
        'etablissements_com_ass': etablissements_com_ass,
        'personnel_hommes': personnel_hommes,
        'personnel_femmes': personnel_femmes,
        'personnel_affecte': personnel_affecte,
        'personnel_non_affecte': personnel_non_affecte,
        'ratio_personnel_etablissement': round(total_personnel / total_etablissements, 1) if total_etablissements > 0 else 0
    }

def get_etablissements_by_type():
    """Répartition des établissements par type"""
    return execute_query("""
        SELECT 
            type_etablissement,
            COUNT(*) as count
        FROM etablissements
        GROUP BY type_etablissement
        ORDER BY count DESC
    """)

def get_etablissements_by_commune():
    """Répartition des établissements par commune (top 10)"""
    return execute_query("""
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

def get_personnel_statistics():
    """Statistiques du personnel"""
    
    # Par corps
    par_corps = execute_query("""
        SELECT 
            corps,
            COUNT(*) as count
        FROM personnel
        WHERE corps IS NOT NULL AND corps != ''
        GROUP BY corps
        ORDER BY count DESC
        LIMIT 8
    """)
    
    # Par grade
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
    
    # Par fonction
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
    
    return {
        'par_corps': par_corps,
        'par_grade': par_grade,
        'par_fonction': par_fonction
    }
