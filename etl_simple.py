#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL Simple pour IEF Louga avec fichiers CSV
Sans dépendances externes (seulement csv et sqlite3)
"""

import csv
import sqlite3
import os

class ETL_Simple:
    def __init__(self, db_path="ief_louga.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect_db(self):
        """Connexion à la base de données SQLite"""
        # Supprimer l'ancienne base si elle existe
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        self.conn = sqlite3.connect(self.db_path)
        print(f"✓ Connexion établie avec {self.db_path}")
        
    def create_tables(self):
        """Création des tables à partir du schéma SQL"""
        with open("schema_bd_ief.sql", "r", encoding="utf-8") as f:
            schema = f.read()
        
        # Exécution du schéma
        self.conn.executescript(schema)
        self.conn.commit()
        print("✓ Tables créées avec succès")
        
    def load_etablissements(self):
        """Chargement et analyse des établissements"""
        print(f"\n🏫 CHARGEMENT DES ÉTABLISSEMENTS")
        print("-" * 40)
        
        etablissements = []
        communes_set = set()
        types_etab = {}
        
        with open('bd/etablissements.csv', 'r', encoding='latin-1') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            for row in reader:
                nom = row.get('nom_etablissement', '').strip()
                if not nom or nom == 'nan':
                    continue
                    
                type_etab = row.get('type_etablissement', '').strip()
                commune = row.get('commune', '').strip()
                arrondissement = row.get('arrondissement', '').strip()
                
                etablissements.append({
                    'nom': nom,
                    'type': type_etab,
                    'commune': commune,
                    'arrondissement': arrondissement,
                    'zone': row.get('zone', '').strip() or None,
                    'statut': row.get('statut', '').strip() or None,
                    'type_statut': row.get('type_statut', '').strip() or None,
                    'directeur': row.get('nom_directeur_complet', '').strip() or None,
                    'contact': row.get('contact_1', '').strip() or None,
                    'email': row.get('email_etablissement', '').strip() or None
                })
                
                if commune and commune != 'nan':
                    communes_set.add((commune, arrondissement))
                
                if type_etab:
                    types_etab[type_etab] = types_etab.get(type_etab, 0) + 1
        
        print(f"   ✓ {len(etablissements)} établissements chargés")
        print(f"   ✓ {len(communes_set)} communes identifiées")
        print(f"   📊 Types: {types_etab}")
        
        return etablissements, communes_set
    
    def load_personnel(self):
        """Chargement et analyse du personnel"""
        print(f"\n👥 CHARGEMENT DU PERSONNEL")
        print("-" * 40)
        
        personnel = []
        specialites = {}
        etablissements_ref = set()
        
        with open('bd/personnels.csv', 'r', encoding='latin-1') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            for row in reader:
                matricule = row.get('matricule', '').strip()
                nom = row.get('nom', '').strip()
                prenom = row.get('prenom', '').strip()
                
                if not matricule or not nom:
                    continue
                
                etablissement = row.get('etablissement', '').strip()
                specialite = row.get('specialite', '').strip()
                
                personnel.append({
                    'matricule': matricule,
                    'nom': nom,
                    'prenom': prenom,
                    'genre': row.get('genre', '').strip() or None,
                    'etablissement': etablissement,
                    'specialite': specialite or None,
                    'grade': row.get('grade', '').strip() or None,
                    'fonction': row.get('fonction', '').strip() or None,
                    'contact': row.get('contact', '').strip() or None,
                    'statut': row.get('statut', '').strip() or None
                })
                
                if etablissement and etablissement != 'nan':
                    etablissements_ref.add(etablissement)
                
                if specialite and specialite != 'nan':
                    specialites[specialite] = specialites.get(specialite, 0) + 1
        
        print(f"   ✓ {len(personnel)} agents chargés")
        print(f"   ✓ {len(etablissements_ref)} établissements référencés")
        print(f"   📊 Top spécialités: {dict(list(specialites.items())[:5])}")
        
        return personnel
    
    def insert_communes(self, communes_set):
        """Insertion des communes"""
        print(f"\n🏙️ INSERTION DES COMMUNES")
        print("-" * 35)
        
        communes_list = [(commune, arrondissement, 'LOUGA') 
                        for commune, arrondissement in communes_set 
                        if commune and commune != 'nan']
        
        cursor = self.conn.cursor()
        cursor.executemany(
            "INSERT OR IGNORE INTO communes (nom, arrondissement, departement) VALUES (?, ?, ?)",
            communes_list
        )
        self.conn.commit()
        
        print(f"   ✓ {len(communes_list)} communes insérées")
        
        # Récupération des IDs
        cursor.execute("SELECT id, nom FROM communes")
        communes_ids = {row[1]: row[0] for row in cursor.fetchall()}
        
        return communes_ids
    
    def insert_etablissements(self, etablissements, communes_ids):
        """Insertion des établissements"""
        print(f"\n🏫 INSERTION DES ÉTABLISSEMENTS")
        print("-" * 35)
        
        etablissements_list = []
        for etab in etablissements:
            commune_id = communes_ids.get(etab['commune'])
            
            etablissements_list.append((
                etab['nom'],
                etab['type'],
                commune_id,
                etab['zone'],
                etab['statut'],
                etab['type_statut'],
                None,  # adresse
                None,  # coordonnees_x
                None,  # coordonnees_y
                etab['directeur'],
                etab['contact'],
                etab['email']
            ))
        
        cursor = self.conn.cursor()
        cursor.executemany("""
            INSERT INTO etablissements (
                nom, type_etablissement, commune_id, zone, statut, type_statut,
                adresse, coordonnees_x, coordonnees_y, directeur, contact_1, email_directeur
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, etablissements_list)
        self.conn.commit()
        
        print(f"   ✓ {len(etablissements_list)} établissements insérés")
        
        # Récupération des IDs
        cursor.execute("SELECT id, nom FROM etablissements")
        etablissements_ids = {row[1]: row[0] for row in cursor.fetchall()}
        
        return etablissements_ids
    
    def insert_personnel(self, personnel, etablissements_ids):
        """Insertion du personnel"""
        print(f"\n👥 INSERTION DU PERSONNEL")
        print("-" * 35)
        
        personnel_list = []
        personnel_non_trouve = 0
        
        for pers in personnel:
            etablissement_id = etablissements_ids.get(pers['etablissement'])
            if not etablissement_id and pers['etablissement']:
                personnel_non_trouve += 1
            
            personnel_list.append((
                pers['matricule'],
                pers['nom'],
                pers['prenom'],
                pers['genre'],
                None,  # date_naissance
                None,  # lieu_naissance
                None,  # numero_cni
                None,  # corps
                pers['grade'],
                pers['fonction'],
                pers['specialite'],
                etablissement_id,
                None,  # service
                pers['contact'],
                None,  # email
                None,  # diplome_academique
                None,  # diplome_professionnel
                None,  # date_entree_enseignement
                None,  # date_arrivee_poste
                None,  # situation_matrimoniale
                None   # nombre_enfants
            ))
        
        cursor = self.conn.cursor()
        cursor.executemany("""
            INSERT INTO personnel (
                matricule, nom, prenom, genre, date_naissance, lieu_naissance,
                numero_cni, corps, grade, fonction, specialite, etablissement_id,
                service, contact, email, diplome_academique, diplome_professionnel,
                date_entree_enseignement, date_arrivee_poste, situation_matrimoniale,
                nombre_enfants
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, personnel_list)
        self.conn.commit()
        
        print(f"   ✓ {len(personnel_list)} agents insérés")
        if personnel_non_trouve > 0:
            print(f"   ⚠️ {personnel_non_trouve} agents sans établissement trouvé")
    
    def print_final_stats(self):
        """Affichage des statistiques finales"""
        print(f"\n📊 STATISTIQUES FINALES")
        print("-" * 35)
        
        cursor = self.conn.cursor()
        
        # Communes
        cursor.execute("SELECT COUNT(*) FROM communes")
        nb_communes = cursor.fetchone()[0]
        
        # Établissements par type
        cursor.execute("""
            SELECT type_etablissement, COUNT(*) 
            FROM etablissements 
            GROUP BY type_etablissement 
            ORDER BY COUNT(*) DESC
        """)
        etablissements_stats = cursor.fetchall()
        
        # Personnel
        cursor.execute("SELECT COUNT(*) FROM personnel")
        nb_personnel = cursor.fetchone()[0]
        
        print(f"   🏙️ Communes: {nb_communes}")
        print(f"   🏫 Établissements par type:")
        total_etablissements = 0
        for type_etab, count in etablissements_stats:
            total_etablissements += count
            print(f"      - {type_etab}: {count}")
        print(f"   📚 Total établissements: {total_etablissements}")
        print(f"   👥 Personnel total: {nb_personnel}")
        if total_etablissements > 0:
            print(f"   📊 Ratio personnel/établissement: {nb_personnel/total_etablissements:.1f}")
    
    def run_etl(self):
        """Exécution complète du processus ETL"""
        print("🚀 DÉMARRAGE ETL IEF LOUGA - VERSION CSV SIMPLE")
        print("=" * 55)
        
        # Connexion et création tables
        self.connect_db()
        self.create_tables()
        
        # Chargement des données
        etablissements, communes_set = self.load_etablissements()
        personnel = self.load_personnel()
        
        # Insertion en base
        communes_ids = self.insert_communes(communes_set)
        etablissements_ids = self.insert_etablissements(etablissements, communes_ids)
        self.insert_personnel(personnel, etablissements_ids)
        
        # Statistiques finales
        self.print_final_stats()
        
        # Fermeture
        self.conn.close()
        print("\n✅ ETL TERMINÉ AVEC SUCCÈS!")

if __name__ == "__main__":
    etl = ETL_Simple()
    etl.run_etl()
