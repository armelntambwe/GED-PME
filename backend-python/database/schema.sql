-- ============================================
-- GED-PME - Schéma de la base de données
-- MySQL - Version pour XAMPP
-- ============================================

-- ==============================
-- 1. TABLE DES UTILISATEURS
-- ==============================
CREATE TABLE IF NOT EXISTS users (
    -- Identifiant unique auto-incrémenté
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Informations personnelles
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,  -- Hash du mot de passe
    
    -- Rôle: définit les permissions
    -- admin_global: super admin
    -- admin_pme: chef d'entreprise
    -- employe: personnel standard
    role ENUM('admin_global', 'admin_pme', 'employe') DEFAULT 'employe',
    
    -- Contact pour notifications SMS (important en RDC)
    telephone VARCHAR(20),
    
    -- Dates
    date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Statut du compte
    actif BOOLEAN DEFAULT TRUE
);

-- ==============================
-- 2. TABLE DES CATÉGORIES
-- ==============================
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- 3. TABLE DES DOCUMENTS
-- ==============================
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Métadonnées du document
    titre VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Informations sur le fichier
    fichier_nom VARCHAR(255),
    fichier_chemin VARCHAR(255),
    fichier_taille INT,
    
    -- Dates
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Statut du document (cycle de vie)
    -- brouillon: en cours d'édition
    -- soumis: en attente de validation
    -- valide: approuvé
    -- rejete: refusé
    -- archive: archivé
    statut ENUM('brouillon', 'soumis', 'valide', 'rejete', 'archive') DEFAULT 'brouillon',
    
    -- Relations
    auteur_id INT NOT NULL,
    categorie_id INT,
    validateur_id INT,
    
    -- Validation
    date_validation DATETIME,
    commentaire_rejet TEXT,
    
    -- Clés étrangères
    FOREIGN KEY (auteur_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (categorie_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (validateur_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ==============================
-- 4. TABLE DES LOGS (Journalisation)
-- ==============================
CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(100) NOT NULL,  -- CREATION, SOUMISSION, VALIDATION, etc.
    description TEXT,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INT NOT NULL,
    document_id INT,
    adresse_ip VARCHAR(45),  -- IPv4 ou IPv6
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
);

-- ==============================
-- 5. INDEX POUR OPTIMISATION
-- ==============================
CREATE INDEX idx_documents_statut ON documents(statut);
CREATE INDEX idx_documents_auteur ON documents(auteur_id);
CREATE INDEX idx_logs_date ON logs(date);