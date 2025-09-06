
-- Base de données IEF LOUGA
-- Création des tables principales

-- Table des communes
CREATE TABLE IF NOT EXISTS communes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom VARCHAR(100) NOT NULL UNIQUE,
    arrondissement VARCHAR(100),
    departement VARCHAR(100) DEFAULT 'LOUGA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des établissements
CREATE TABLE IF NOT EXISTS etablissements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom VARCHAR(200) NOT NULL,
    code VARCHAR(50),
    type_etablissement VARCHAR(50), -- elementaire, prescolaire, moyen_second, daara, formation_prof
    cycle VARCHAR(50),
    statut VARCHAR(50), -- Public, Privé
    type_statut VARCHAR(100),
    commune_id INTEGER,
    zone VARCHAR(100),
    adresse TEXT,
    coordonnees_x DECIMAL(10,2),
    coordonnees_y DECIMAL(10,2),
    directeur VARCHAR(200),
    contact_1 VARCHAR(20),
    contact_2 VARCHAR(20),
    email_directeur VARCHAR(200),
    date_creation DATE,
    date_ouverture DATE,
    observations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (commune_id) REFERENCES communes(id)
);

-- Table du personnel
CREATE TABLE IF NOT EXISTS personnel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricule VARCHAR(50) UNIQUE,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    genre VARCHAR(10),
    date_naissance DATE,
    lieu_naissance VARCHAR(200),
    numero_cni VARCHAR(50),
    corps VARCHAR(50),
    grade VARCHAR(50),
    fonction VARCHAR(100),
    specialite VARCHAR(100),
    etablissement_id INTEGER, -- NULL pour personnel IEF
    service VARCHAR(100), -- Pour personnel IEF
    contact VARCHAR(50),
    email VARCHAR(200),
    diplome_academique VARCHAR(100),
    diplome_professionnel VARCHAR(100),
    date_entree_enseignement DATE,
    date_arrivee_poste DATE,
    situation_matrimoniale VARCHAR(50),
    nombre_enfants INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (etablissement_id) REFERENCES etablissements(id)
);

-- Table d'historique des affectations
CREATE TABLE IF NOT EXISTS affectations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personnel_id INTEGER NOT NULL,
    etablissement_id INTEGER,
    service VARCHAR(100), -- Pour affectations IEF
    fonction_specifique VARCHAR(100),
    date_debut DATE NOT NULL,
    date_fin DATE,
    observations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (personnel_id) REFERENCES personnel(id),
    FOREIGN KEY (etablissement_id) REFERENCES etablissements(id)
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_personnel_matricule ON personnel(matricule);
CREATE INDEX IF NOT EXISTS idx_personnel_etablissement ON personnel(etablissement_id);
CREATE INDEX IF NOT EXISTS idx_etablissements_commune ON etablissements(commune_id);
CREATE INDEX IF NOT EXISTS idx_etablissements_type ON etablissements(type_etablissement);
CREATE INDEX IF NOT EXISTS idx_affectations_personnel ON affectations(personnel_id);

-- Vues utiles
CREATE VIEW IF NOT EXISTS vue_personnel_complet AS
SELECT 
    p.*,
    e.nom as nom_etablissement,
    e.type_etablissement,
    c.nom as commune,
    c.arrondissement
FROM personnel p
LEFT JOIN etablissements e ON p.etablissement_id = e.id
LEFT JOIN communes c ON e.commune_id = c.id;

CREATE VIEW IF NOT EXISTS vue_etablissements_complet AS
SELECT 
    e.*,
    c.nom as commune,
    c.arrondissement,
    COUNT(p.id) as nombre_personnel
FROM etablissements e
LEFT JOIN communes c ON e.commune_id = c.id
LEFT JOIN personnel p ON e.id = p.etablissement_id
GROUP BY e.id;
