#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blueprint Rapports - Génération de rapports et analyses
"""

from flask import Blueprint, render_template, jsonify, send_file, make_response
import sqlite3
import json
import io
import os
import csv
from datetime import datetime

rapports_bp = Blueprint('rapports', __name__)

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

@rapports_bp.route('/')
def index():
    """Page principale des rapports"""
    
    # Statistiques pour la page d'accueil
    stats = execute_query_single("""
        SELECT 
            (SELECT COUNT(*) FROM etablissements) as total_etablissements,
            (SELECT COUNT(*) FROM personnel) as total_personnel,
            (SELECT COUNT(*) FROM communes) as total_communes,
            (SELECT COUNT(*) FROM etablissements WHERE statut LIKE '%Public%') as etablissements_publics,
            (SELECT COUNT(*) FROM etablissements WHERE statut LIKE '%Privé%') as etablissements_prives,
            (SELECT COUNT(*) FROM etablissements WHERE statut LIKE '%Com_Ass%' OR statut LIKE '%Communautaire%') as etablissements_communautaires,
            (SELECT COUNT(*) FROM personnel WHERE etablissement_id IS NOT NULL OR service IS NOT NULL) as personnel_affecte,
            (SELECT COUNT(*) FROM personnel WHERE etablissement_id IS NULL AND (service IS NULL OR service = '')) as personnel_non_affecte
    """)
    
    # Rapports disponibles
    rapports_liste = [
        {
            'id': 'synthese',
            'titre': 'Rapport de Synthèse Générale',
            'description': 'Vue d\'ensemble complète de l\'IEF Louga',
            'icone': 'fas fa-chart-pie'
        },
        {
            'id': 'etablissements',
            'titre': 'Analyse des Établissements',
            'description': 'Répartition et analyse des établissements par type et commune',
            'icone': 'fas fa-school'
        },
        {
            'id': 'personnel',
            'titre': 'Analyse du Personnel',
            'description': 'Effectifs, répartition et qualifications du personnel',
            'icone': 'fas fa-users'
        },
        {
            'id': 'couverture',
            'titre': 'Couverture Territoriale',
            'description': 'Analyse de la répartition géographique',
            'icone': 'fas fa-map-marked-alt'
        },
        {
            'id': 'indicateurs',
            'titre': 'Indicateurs de Performance',
            'description': 'KPIs et métriques clés de l\'IEF',
            'icone': 'fas fa-tachometer-alt'
        }
    ]
    
    # Heure actuelle pour l'affichage
    from datetime import datetime
    current_time = datetime.now().strftime("%d/%m/%Y à %H:%M")
    
    return render_template('rapports/index.html', 
                         rapports=rapports_liste, 
                         stats=stats,
                         current_time=current_time)

@rapports_bp.route('/synthese')
def synthese():
    """Rapport de synthèse générale"""
    
    # Données de synthèse
    donnees = generer_rapport_synthese()
    
    return render_template('rapports/synthese.html', donnees=donnees)

@rapports_bp.route('/etablissements')
def rapport_etablissements():
    """Rapport détaillé sur les établissements"""
    
    donnees = generer_rapport_etablissements()
    
    return render_template('rapports/etablissements.html', donnees=donnees)

@rapports_bp.route('/personnel')
def rapport_personnel():
    """Rapport détaillé sur le personnel"""
    
    donnees = generer_rapport_personnel()
    
    return render_template('rapports/personnel.html', donnees=donnees)

@rapports_bp.route('/couverture')
def rapport_couverture():
    """Rapport de couverture territoriale"""
    
    donnees = generer_rapport_couverture()
    
    return render_template('rapports/couverture.html', donnees=donnees)

@rapports_bp.route('/indicateurs')
def rapport_indicateurs():
    """Rapport des indicateurs de performance"""
    
    donnees = generer_rapport_indicateurs()
    
    return render_template('rapports/indicateurs.html', donnees=donnees)

@rapports_bp.route('/api/synthese')
def api_rapport_synthese():
    """API pour le rapport de synthèse"""
    donnees = generer_rapport_synthese()
    return jsonify(donnees)

# Routes d'export
@rapports_bp.route('/api/export/complete-excel')
def export_complete_excel():
    """Export complet en Excel - Version simplifiée"""
    try:
        # Pour l'instant, on retourne les données en JSON
        # Plus tard, on ajoutera l'export Excel quand les modules seront installés
        
        # Récupérer toutes les données
        etablissements = execute_query("""
            SELECT 
                e.nom,
                e.type_etablissement,
                e.statut,
                c.nom as commune,
                c.arrondissement,
                e.directeur,
                e.contact_1,
                e.email_directeur
            FROM etablissements e
            LEFT JOIN communes c ON e.commune_id = c.id
            ORDER BY c.arrondissement, c.nom, e.nom
        """)
        
        personnel = execute_query("""
            SELECT 
                p.prenom,
                p.nom,
                p.genre,
                p.corps,
                p.grade,
                p.service,
                e.nom as etablissement
            FROM personnel p
            LEFT JOIN etablissements e ON p.etablissement_id = e.id
            ORDER BY p.nom, p.prenom
        """)
        
        stats = generer_rapport_synthese()
        
        # Créer un fichier CSV simple pour l'instant
        import csv
        import io
        
        output = io.StringIO()
        
        # Écrire les établissements
        output.write("=== ÉTABLISSEMENTS ===\n")
        writer = csv.writer(output)
        writer.writerow(['Nom', 'Type', 'Statut', 'Commune', 'Arrondissement', 'Directeur', 'Contact', 'Email'])
        
        for etab in etablissements:
            writer.writerow([
                etab['nom'], etab['type_etablissement'], etab['statut'],
                etab['commune'], etab['arrondissement'], etab['directeur'],
                etab['contact_1'], etab['email_directeur']
            ])
        
        output.write("\n\n=== PERSONNEL ===\n")
        writer.writerow(['Prénom', 'Nom', 'Genre', 'Corps', 'Grade', 'Service', 'Établissement'])
        
        for pers in personnel:
            writer.writerow([
                pers['prenom'], pers['nom'], pers['genre'], pers['corps'],
                pers['grade'], pers['service'], pers['etablissement']
            ])
        
        # Créer la réponse
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=rapport_ief_louga_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'export: {str(e)}'}), 500

@rapports_bp.route('/api/export/executive-pdf')
def export_executive_pdf():
    """Export du rapport exécutif en PDF - Version simplifiée"""
    try:
        # Pour l'instant, on génère un rapport HTML qui peut être imprimé en PDF
        stats_data = generer_rapport_synthese()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Rapport Exécutif IEF Louga</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2563eb; text-align: center; }}
                h2 {{ color: #1f2937; border-bottom: 2px solid #e5e7eb; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
                th {{ background-color: #f3f4f6; font-weight: bold; }}
                .summary {{ background-color: #f0f9ff; padding: 15px; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <h1>RAPPORT EXÉCUTIF - IEF LOUGA</h1>
            <p><strong>Généré le:</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
            
            <div class="summary">
                <h2>Synthèse Exécutive</h2>
        """
        
        chiffres = stats_data.get('chiffres_cles', {})
        if chiffres:
            html_content += f"""
                <table>
                    <tr><th>Indicateur</th><th>Valeur</th></tr>
                    <tr><td>Total Établissements</td><td>{chiffres.get('total_etablissements', 0)}</td></tr>
                    <tr><td>Total Personnel</td><td>{chiffres.get('total_personnel', 0)}</td></tr>
                    <tr><td>Total Communes</td><td>{chiffres.get('total_communes', 0)}</td></tr>
                    <tr><td>Établissements Publics</td><td>{chiffres.get('etablissements_publics', 0)}</td></tr>
                    <tr><td>Établissements Privés</td><td>{chiffres.get('etablissements_prives', 0)}</td></tr>
                    <tr><td>Personnel Hommes</td><td>{chiffres.get('personnel_hommes', 0)}</td></tr>
                    <tr><td>Personnel Femmes</td><td>{chiffres.get('personnel_femmes', 0)}</td></tr>
                </table>
            """
        
        etab_types = stats_data.get('etablissements_par_type', [])
        if etab_types:
            html_content += """
                <h2>Répartition par Type d'Établissement</h2>
                <table>
                    <tr><th>Type d'Établissement</th><th>Nombre</th><th>Pourcentage</th></tr>
            """
            for item in etab_types:
                html_content += f"""
                    <tr>
                        <td>{item['type_etablissement']}</td>
                        <td>{item['count']}</td>
                        <td>{item['pourcentage']}%</td>
                    </tr>
                """
            html_content += "</table>"
        
        html_content += """
            </div>
            <br>
            <p><em>Rapport généré automatiquement par le système IEF Louga.</em></p>
            <p><em>Pour convertir en PDF, utilisez la fonction d'impression de votre navigateur.</em></p>
        </body>
        </html>
        """
        
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'export PDF: {str(e)}'}), 500

def generer_rapport_synthese():
    """Génère les données du rapport de synthèse"""
    
    # Chiffres clés
    chiffres_cles = execute_query_single("""
        SELECT 
            (SELECT COUNT(*) FROM etablissements) as total_etablissements,
            (SELECT COUNT(*) FROM personnel) as total_personnel,
            (SELECT COUNT(*) FROM communes) as total_communes,
            (SELECT COUNT(*) FROM etablissements WHERE statut LIKE '%Public%') as etablissements_publics,
            (SELECT COUNT(*) FROM etablissements WHERE statut LIKE '%Privé%') as etablissements_prives,
            (SELECT COUNT(*) FROM personnel WHERE genre IN ('M', 'H')) as personnel_hommes,
            (SELECT COUNT(*) FROM personnel WHERE genre = 'F') as personnel_femmes
    """)
    
    # Répartition établissements par type
    etablissements_par_type = execute_query("""
        SELECT 
            type_etablissement,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM etablissements), 1) as pourcentage
        FROM etablissements
        GROUP BY type_etablissement
        ORDER BY count DESC
    """)
    
    # Top 10 communes
    top_communes = execute_query("""
        SELECT 
            c.nom as commune,
            c.arrondissement,
            COUNT(e.id) as nombre_etablissements,
            COUNT(p.id) as nombre_personnel
        FROM communes c
        LEFT JOIN etablissements e ON c.id = e.commune_id
        LEFT JOIN personnel p ON e.id = p.etablissement_id
        GROUP BY c.id, c.nom, c.arrondissement
        HAVING nombre_etablissements > 0
        ORDER BY nombre_etablissements DESC
        LIMIT 10
    """)
    
    # Évolution des effectifs (simulation - à remplacer par vraies données historiques)
    evolution_effectifs = [
        {'annee': 2020, 'etablissements': 750, 'personnel': 2800},
        {'annee': 2021, 'etablissements': 760, 'personnel': 2850},
        {'annee': 2022, 'etablissements': 765, 'personnel': 2870},
        {'annee': 2023, 'etablissements': 769, 'personnel': 2882}
    ]
    
    return {
        'chiffres_cles': chiffres_cles,
        'etablissements_par_type': etablissements_par_type,
        'top_communes': top_communes,
        'evolution_effectifs': evolution_effectifs
    }

def generer_rapport_etablissements():
    """Génère les données du rapport établissements"""
    
    # Analyse par type et statut
    analyse_type_statut = execute_query("""
        SELECT 
            type_etablissement,
            statut,
            COUNT(*) as count
        FROM etablissements
        WHERE statut IS NOT NULL
        GROUP BY type_etablissement, statut
        ORDER BY type_etablissement, count DESC
    """)
    
    # Géolocalisation
    geo_analyse = execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN coordonnees_x IS NOT NULL THEN 1 END) as avec_coordonnees,
            ROUND(COUNT(CASE WHEN coordonnees_x IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 1) as taux_geolocalisation
        FROM etablissements
    """)
    
    # Établissements par commune et type
    repartition_communale = execute_query("""
        SELECT 
            c.nom as commune,
            c.arrondissement,
            e.type_etablissement,
            COUNT(e.id) as count
        FROM communes c
        LEFT JOIN etablissements e ON c.id = e.commune_id
        WHERE e.id IS NOT NULL
        GROUP BY c.nom, c.arrondissement, e.type_etablissement
        ORDER BY c.nom, count DESC
    """)
    
    # Directeurs et contacts
    responsables_analyse = execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN directeur IS NOT NULL AND directeur != '' THEN 1 END) as avec_directeur,
            COUNT(CASE WHEN contact_1 IS NOT NULL AND contact_1 != '' THEN 1 END) as avec_contact,
            COUNT(CASE WHEN email_directeur IS NOT NULL AND email_directeur != '' THEN 1 END) as avec_email
        FROM etablissements
    """)
    
    return {
        'analyse_type_statut': analyse_type_statut,
        'geo_analyse': geo_analyse,
        'repartition_communale': repartition_communale,
        'responsables_analyse': responsables_analyse
    }

def generer_rapport_personnel():
    """Génère les données du rapport personnel"""
    
    # Analyse par corps et grade
    corps_grade = execute_query("""
        SELECT 
            corps,
            grade,
            COUNT(*) as count,
            COUNT(CASE WHEN genre IN ('M', 'H') THEN 1 END) as hommes,
            COUNT(CASE WHEN genre = 'F' THEN 1 END) as femmes
        FROM personnel
        WHERE corps IS NOT NULL AND grade IS NOT NULL
        GROUP BY corps, grade
        ORDER BY corps, count DESC
    """)
    
    # Répartition par type d'affectation
    affectations = execute_query_single("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN etablissement_id IS NOT NULL THEN 1 END) as affectes_etablissement,
            COUNT(CASE WHEN service IS NOT NULL AND service != '' THEN 1 END) as affectes_service,
            COUNT(CASE WHEN etablissement_id IS NULL AND (service IS NULL OR service = '') THEN 1 END) as non_affectes
        FROM personnel
    """)
    
    # Qualifications
    qualifications = execute_query("""
        SELECT 
            diplome_academique,
            diplome_professionnel,
            COUNT(*) as count
        FROM personnel
        WHERE diplome_academique IS NOT NULL OR diplome_professionnel IS NOT NULL
        GROUP BY diplome_academique, diplome_professionnel
        ORDER BY count DESC
        LIMIT 15
    """)
    
    # Ancienneté (approximative)
    anciennete = execute_query("""
        SELECT 
            CASE 
                WHEN date_entree_enseignement IS NULL THEN 'Non renseigné'
                WHEN CAST(SUBSTR(date_entree_enseignement, 1, 4) AS INTEGER) >= 2015 THEN 'Moins de 10 ans'
                WHEN CAST(SUBSTR(date_entree_enseignement, 1, 4) AS INTEGER) >= 2005 THEN '10-20 ans'
                WHEN CAST(SUBSTR(date_entree_enseignement, 1, 4) AS INTEGER) >= 1995 THEN '20-30 ans'
                ELSE 'Plus de 30 ans'
            END as tranche_anciennete,
            COUNT(*) as count
        FROM personnel
        GROUP BY 
            CASE 
                WHEN date_entree_enseignement IS NULL THEN 'Non renseigné'
                WHEN CAST(SUBSTR(date_entree_enseignement, 1, 4) AS INTEGER) >= 2015 THEN 'Moins de 10 ans'
                WHEN CAST(SUBSTR(date_entree_enseignement, 1, 4) AS INTEGER) >= 2005 THEN '10-20 ans'
                WHEN CAST(SUBSTR(date_entree_enseignement, 1, 4) AS INTEGER) >= 1995 THEN '20-30 ans'
                ELSE 'Plus de 30 ans'
            END
        ORDER BY count DESC
    """)
    
    return {
        'corps_grade': corps_grade,
        'affectations': affectations,
        'qualifications': qualifications,
        'anciennete': anciennete
    }

def generer_rapport_couverture():
    """Génère les données du rapport de couverture territoriale"""
    
    # Couverture par arrondissement
    par_arrondissement = execute_query("""
        SELECT 
            c.arrondissement,
            COUNT(DISTINCT c.id) as nombre_communes,
            COUNT(e.id) as nombre_etablissements,
            COUNT(p.id) as nombre_personnel,
            ROUND(AVG(CASE WHEN e.id IS NOT NULL THEN 1.0 ELSE 0.0 END) * 100, 1) as taux_couverture
        FROM communes c
        LEFT JOIN etablissements e ON c.id = e.commune_id
        LEFT JOIN personnel p ON e.id = p.etablissement_id
        GROUP BY c.arrondissement
        ORDER BY nombre_etablissements DESC
    """)
    
    # Densité par commune
    densite_communale = execute_query("""
        SELECT 
            c.nom as commune,
            c.arrondissement,
            COUNT(e.id) as nombre_etablissements,
            COUNT(p.id) as nombre_personnel,
            ROUND(CAST(COUNT(p.id) AS FLOAT) / NULLIF(COUNT(e.id), 0), 1) as ratio_personnel_etablissement
        FROM communes c
        LEFT JOIN etablissements e ON c.id = e.commune_id
        LEFT JOIN personnel p ON e.id = p.etablissement_id
        GROUP BY c.id, c.nom, c.arrondissement
        HAVING nombre_etablissements > 0
        ORDER BY nombre_etablissements DESC
    """)
    
    # Analyse des zones non couvertes ou sous-couvertes
    zones_critique = execute_query("""
        SELECT 
            c.nom as commune,
            c.arrondissement,
            COUNT(e.id) as nombre_etablissements,
            COUNT(DISTINCT e.type_etablissement) as types_disponibles
        FROM communes c
        LEFT JOIN etablissements e ON c.id = e.commune_id
        GROUP BY c.id, c.nom, c.arrondissement
        HAVING nombre_etablissements < 5 OR types_disponibles < 2
        ORDER BY nombre_etablissements ASC
    """)
    
    return {
        'par_arrondissement': par_arrondissement,
        'densite_communale': densite_communale,
        'zones_critique': zones_critique
    }

def generer_rapport_indicateurs():
    """Génère les données du rapport d'indicateurs"""
    
    # KPIs principaux
    kpis = execute_query_single("""
        SELECT 
            ROUND(CAST((SELECT COUNT(*) FROM personnel) AS FLOAT) / (SELECT COUNT(*) FROM etablissements), 1) as ratio_personnel_etablissement,
            ROUND(CAST((SELECT COUNT(*) FROM etablissements) AS FLOAT) / (SELECT COUNT(*) FROM communes), 1) as ratio_etablissement_commune,
            ROUND((SELECT COUNT(*) FROM etablissements WHERE statut LIKE '%Public%') * 100.0 / (SELECT COUNT(*) FROM etablissements), 1) as taux_public,
            ROUND((SELECT COUNT(*) FROM personnel WHERE genre = 'F') * 100.0 / (SELECT COUNT(*) FROM personnel WHERE genre IS NOT NULL), 1) as taux_feminisation,
            ROUND((SELECT COUNT(*) FROM etablissements WHERE coordonnees_x IS NOT NULL) * 100.0 / (SELECT COUNT(*) FROM etablissements), 1) as taux_geolocalisation,
            ROUND((SELECT COUNT(*) FROM personnel WHERE etablissement_id IS NOT NULL OR service IS NOT NULL) * 100.0 / (SELECT COUNT(*) FROM personnel), 1) as taux_affectation
    """)
    
    # Évolution des KPIs (simulation)
    evolution_kpis = [
        {'indicateur': 'Ratio Personnel/Établissement', 'valeur_2023': 3.7, 'objectif': 4.0, 'tendance': 'stable'},
        {'indicateur': 'Taux de Géolocalisation (%)', 'valeur_2023': 95.9, 'objectif': 100.0, 'tendance': 'amélioration'},
        {'indicateur': 'Taux d\'Affectation (%)', 'valeur_2023': 54.7, 'objectif': 85.0, 'tendance': 'à améliorer'},
        {'indicateur': 'Couverture Communale (%)', 'valeur_2023': 94.1, 'objectif': 100.0, 'tendance': 'stable'}
    ]
    
    # Benchmarks par type d'établissement
    benchmarks = execute_query("""
        SELECT 
            type_etablissement,
            COUNT(*) as nombre,
            ROUND(AVG(nombre_personnel), 1) as personnel_moyen,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM etablissements), 1) as pourcentage_total
        FROM (
            SELECT 
                e.type_etablissement,
                (SELECT COUNT(*) FROM personnel p WHERE p.etablissement_id = e.id) as nombre_personnel
            FROM etablissements e
        ) as subq
        GROUP BY type_etablissement
        ORDER BY nombre DESC
    """)
    
    return {
        'kpis': kpis,
        'evolution_kpis': evolution_kpis,
        'benchmarks': benchmarks
    }
