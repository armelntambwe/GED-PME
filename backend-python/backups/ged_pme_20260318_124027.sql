-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: ged_pme
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(50) NOT NULL,
  `description` text DEFAULT NULL,
  `date_creation` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `nom` (`nom`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,'Factures','Documents comptables et factures','2026-03-09 17:50:55'),(2,'RH','Ressources humaines - contrats, CV, évaluations','2026-03-09 17:51:14'),(3,'Contrats','Contrats clients et fournisseurs','2026-03-09 17:51:30');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `documents`
--

DROP TABLE IF EXISTS `documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `documents` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `titre` varchar(200) NOT NULL,
  `description` text DEFAULT NULL,
  `fichier_nom` varchar(255) DEFAULT NULL,
  `fichier_chemin` varchar(255) DEFAULT NULL,
  `fichier_taille` int(11) DEFAULT NULL,
  `type_mime` varchar(100) DEFAULT NULL,
  `date_creation` datetime DEFAULT current_timestamp(),
  `statut` enum('brouillon','soumis','valide','rejete','archive') DEFAULT 'brouillon',
  `auteur_id` int(11) NOT NULL,
  `categorie_id` int(11) DEFAULT NULL,
  `validateur_id` int(11) DEFAULT NULL,
  `date_validation` datetime DEFAULT NULL,
  `commentaire_rejet` text DEFAULT NULL,
  `niveau_validation_actuel` int(11) DEFAULT 1,
  `workflow_termine` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `auteur_id` (`auteur_id`),
  CONSTRAINT `documents_ibfk_1` FOREIGN KEY (`auteur_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `documents`
--

LOCK TABLES `documents` WRITE;
/*!40000 ALTER TABLE `documents` DISABLE KEYS */;
INSERT INTO `documents` VALUES (1,'Facture Decembre','Facture fournisseur',NULL,NULL,NULL,NULL,'2026-03-04 17:25:16','valide',1,NULL,1,'2026-03-04 17:39:04',NULL,1,0),(2,'Facture Janvier','Facture client A',NULL,NULL,NULL,NULL,'2026-03-04 17:27:07','rejete',3,NULL,1,NULL,'Signature manquante',1,0),(3,'Rapport mensuel','Rapport janvier 2024',NULL,NULL,NULL,NULL,'2026-03-04 17:27:08','valide',3,NULL,4,'2026-03-04 17:39:59',NULL,1,0),(4,'Contrat Client B','Contrat de service',NULL,NULL,NULL,NULL,'2026-03-04 17:27:12','brouillon',3,NULL,NULL,NULL,NULL,1,0),(5,'Test cycle','Document test',NULL,NULL,NULL,NULL,'2026-03-04 17:42:26','valide',3,NULL,1,'2026-03-04 17:42:27',NULL,1,0),(6,'Document test avec JWT','',NULL,NULL,NULL,NULL,'2026-03-05 21:42:26','soumis',5,NULL,NULL,NULL,NULL,1,0),(7,'Document test','Test avec fichier texte','test.txt','uploads\\5_1772915584_test.txt',20,'text/plain','2026-03-07 21:33:04','brouillon',5,NULL,NULL,NULL,NULL,1,0),(8,'Document PDF test','Test avec vrai PDF','1.3. Procedures et Fonctions.pdf','uploads\\5_1772915699_1.3._Procedures_et_Fonctions.pdf',694571,'application/pdf','2026-03-07 21:34:59','brouillon',5,NULL,NULL,NULL,NULL,1,0),(9,'Document avec log','','test.txt','uploads\\6_1773081922_test.txt',46,'text/plain','2026-03-09 19:45:22','soumis',6,NULL,NULL,NULL,NULL,1,0),(10,'Document avec log','','test.txt','uploads\\6_1773081998_test.txt',20,'text/plain','2026-03-09 19:46:39','rejete',6,NULL,6,NULL,'Document incomplet, veuillez recommencer',1,0),(11,'Document avec log','','test.txt','uploads\\6_1773082121_test.txt',46,'text/plain','2026-03-09 19:48:41','brouillon',6,NULL,NULL,NULL,NULL,1,0),(12,'Document pour test rejet','','test.txt','uploads\\6_1773082747_test.txt',46,'text/plain','2026-03-09 19:59:07','brouillon',6,NULL,NULL,NULL,NULL,1,0),(13,'Document workflow test','','test.txt','uploads\\6_1773086976_test.txt',46,'text/plain','2026-03-09 21:09:36','soumis',6,NULL,NULL,NULL,NULL,1,0),(14,'Document workflow test 2','','test.txt','uploads\\6_1773087359_test.txt',46,'text/plain','2026-03-09 21:15:59','soumis',6,NULL,NULL,NULL,NULL,1,0),(15,'Document workflow test 2','','test.txt','uploads\\6_1773087409_test.txt',46,'text/plain','2026-03-09 21:16:49','valide',6,NULL,NULL,NULL,NULL,3,1),(16,'Test workflow final','','test.txt','uploads\\6_1773088747_test.txt',46,'text/plain','2026-03-09 21:39:07','brouillon',6,NULL,NULL,NULL,NULL,1,0),(17,'Test','','test.txt','uploads\\6_1773165826_test.txt',4,'text/plain','2026-03-10 19:03:49','brouillon',6,NULL,NULL,NULL,NULL,1,0),(18,'Test','','test.txt','uploads\\6_1773165826_test.txt',4,'text/plain','2026-03-10 19:03:49','brouillon',6,NULL,NULL,NULL,NULL,1,0),(19,'Test','','test.txt','uploads\\6_1773165825_test.txt',4,'text/plain','2026-03-10 19:03:49','brouillon',6,NULL,NULL,NULL,NULL,1,0),(20,'Test','','test.txt','uploads\\6_1773165826_test.txt',4,'text/plain','2026-03-10 19:03:49','brouillon',6,NULL,NULL,NULL,NULL,1,0),(21,'Test','','test.txt','uploads\\6_1773165825_test.txt',4,'text/plain','2026-03-10 19:03:49','brouillon',6,NULL,NULL,NULL,NULL,1,0),(22,'Test','','test.txt','uploads\\6_1773165826_test.txt',4,'text/plain','2026-03-10 19:03:49','brouillon',6,NULL,NULL,NULL,NULL,1,0),(23,'Test','','test.txt','uploads\\6_1773165830_test.txt',4,'text/plain','2026-03-10 19:03:51','brouillon',6,NULL,NULL,NULL,NULL,1,0),(24,'Test','','test.txt','uploads\\6_1773165831_test.txt',4,'text/plain','2026-03-10 19:03:53','brouillon',6,NULL,NULL,NULL,NULL,1,0),(25,'Test','','test.txt','uploads\\6_1773165833_test.txt',4,'text/plain','2026-03-10 19:03:53','brouillon',6,NULL,NULL,NULL,NULL,1,0),(26,'Test','','test.txt','uploads\\6_1773165833_test.txt',4,'text/plain','2026-03-10 19:03:53','brouillon',6,NULL,NULL,NULL,NULL,1,0),(27,'Test','','test.txt','uploads\\6_1773165833_test.txt',4,'text/plain','2026-03-10 19:03:53','brouillon',6,NULL,NULL,NULL,NULL,1,0),(28,'Test','','test.txt','uploads\\6_1773165833_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,1,0),(29,'Test','','test.txt','uploads\\6_1773165834_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,1,0),(30,'Test','','test.txt','uploads\\6_1773165834_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,1,0),(31,'Test','','test.txt','uploads\\6_1773165834_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,1,0),(32,'Test','','test.txt','uploads\\6_1773165834_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,1,0),(33,'Test','','test.txt','uploads\\6_1773165834_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,1,0),(34,'Test','','test.txt','uploads\\6_1773165834_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,1,0),(35,'Test','','test.txt','uploads\\6_1773165835_test.txt',4,'text/plain','2026-03-10 19:03:55','brouillon',6,NULL,NULL,NULL,NULL,1,0),(36,'Test','','test.txt','uploads\\6_1773166107_test.txt',4,'text/plain','2026-03-10 19:08:27','brouillon',6,NULL,NULL,NULL,NULL,1,0),(37,'Test','','test.txt','uploads\\6_1773215904_test.txt',4,'text/plain','2026-03-11 08:58:24','brouillon',6,NULL,NULL,NULL,NULL,1,0),(38,'Test','','test.txt','uploads\\6_1773222667_test.txt',4,'text/plain','2026-03-11 10:51:07','brouillon',6,NULL,NULL,NULL,NULL,1,0),(39,'Test','','test.txt','uploads\\6_1773674794_test.txt',4,'text/plain','2026-03-16 16:26:34','brouillon',6,NULL,NULL,NULL,NULL,1,0),(40,'Test','','test.txt','uploads\\6_1773674803_test.txt',4,'text/plain','2026-03-16 16:26:43','brouillon',6,NULL,NULL,NULL,NULL,1,0),(41,'Test','','test.txt','uploads\\6_1773674809_test.txt',4,'text/plain','2026-03-16 16:26:49','brouillon',6,NULL,NULL,NULL,NULL,1,0),(42,'Test','','test.txt','uploads\\6_1773674817_test.txt',4,'text/plain','2026-03-16 16:26:57','brouillon',6,NULL,NULL,NULL,NULL,1,0),(43,'Test','','test.txt','uploads\\6_1773674821_test.txt',4,'text/plain','2026-03-16 16:27:01','brouillon',6,NULL,NULL,NULL,NULL,1,0),(44,'Test','','test.txt','uploads\\6_1773674824_test.txt',4,'text/plain','2026-03-16 16:27:04','brouillon',6,NULL,NULL,NULL,NULL,1,0),(45,'Test après connexion','','nouveau_test.txt','uploads\\6_1773825315_nouveau_test.txt',38,'text/plain','2026-03-18 10:15:15','brouillon',6,NULL,NULL,NULL,NULL,1,0),(46,'Document créé hors-ligne','','test_offline.txt','uploads\\6_1773829366_test_offline.txt',38,'text/plain','2026-03-18 11:22:48','brouillon',6,NULL,NULL,NULL,NULL,1,0);
/*!40000 ALTER TABLE `documents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `entreprises`
--

DROP TABLE IF EXISTS `entreprises`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `entreprises` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `adresse` text DEFAULT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `date_creation` datetime DEFAULT current_timestamp(),
  `statut` enum('actif','suspendu') DEFAULT 'actif',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entreprises`
--

LOCK TABLES `entreprises` WRITE;
/*!40000 ALTER TABLE `entreprises` DISABLE KEYS */;
INSERT INTO `entreprises` VALUES (1,'Entreprise Test','Kinshasa','+243811111111','contact@test.cd','2026-03-09 20:44:19','actif');
/*!40000 ALTER TABLE `entreprises` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `logs`
--

DROP TABLE IF EXISTS `logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `date` datetime DEFAULT current_timestamp(),
  `user_id` int(11) NOT NULL,
  `document_id` int(11) DEFAULT NULL,
  `adresse_ip` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=52 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `logs`
--

LOCK TABLES `logs` WRITE;
/*!40000 ALTER TABLE `logs` DISABLE KEYS */;
INSERT INTO `logs` VALUES (1,'CREATION','Document \'Document avec log\' uploadé','2026-03-09 19:45:23',6,9,NULL),(2,'CREATION','Document \'Document avec log\' uploadé','2026-03-09 19:46:39',6,10,NULL),(3,'CREATION','Document \'Document avec log\' uploadé','2026-03-09 19:48:41',6,11,NULL),(4,'SOUMISSION','Document 9 soumis','2026-03-09 19:50:35',6,9,NULL),(5,'TELECHARGEMENT','Document 9 téléchargé','2026-03-09 19:52:55',6,9,NULL),(6,'CREATION','Document \'Document pour test rejet\' uploadé','2026-03-09 19:59:07',6,12,NULL),(7,'SOUMISSION','Document 10 soumis','2026-03-09 19:59:23',6,10,NULL),(8,'REJET','Document 10 rejeté: Document incomplet, veuillez recommencer','2026-03-09 19:59:39',6,10,NULL),(9,'CONFIG_WORKFLOW','Workflow configuré avec 3 étapes','2026-03-09 21:06:43',6,NULL,NULL),(10,'CREATION','Document \'Document workflow test\' uploadé','2026-03-09 21:09:36',6,13,NULL),(11,'SOUMISSION','Document 13 soumis','2026-03-09 21:10:47',6,13,NULL),(12,'CONFIG_WORKFLOW','Workflow configuré avec 3 étapes','2026-03-09 21:14:15',6,NULL,NULL),(13,'CONFIG_WORKFLOW','Workflow configuré avec 3 étapes','2026-03-09 21:14:26',6,NULL,NULL),(14,'CREATION','Document \'Document workflow test 2\' uploadé','2026-03-09 21:15:59',6,14,NULL),(15,'SOUMISSION','Document 14 soumis','2026-03-09 21:16:34',6,14,NULL),(16,'CREATION','Document \'Document workflow test 2\' uploadé','2026-03-09 21:16:49',6,15,NULL),(17,'CREATION','Document \'Test workflow final\' uploadé','2026-03-09 21:39:07',6,16,NULL),(18,'SOUMISSION','Document 15 soumis','2026-03-09 21:39:40',6,15,NULL),(19,'VALIDATION_ETAPE','Document 15 - Étape 1/3 validée','2026-03-09 21:48:24',7,15,NULL),(20,'VALIDATION_ETAPE','Document 15 - Étape 2/3 validée','2026-03-09 21:52:56',8,15,NULL),(21,'VALIDATION_ETAPE','Document 15 - Étape 3/3 validée','2026-03-09 21:53:49',6,15,NULL),(22,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:50',6,20,NULL),(23,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:50',6,18,NULL),(24,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:50',6,22,NULL),(25,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:50',6,17,NULL),(26,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:50',6,21,NULL),(27,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:50',6,19,NULL),(28,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:53',6,23,NULL),(29,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:53',6,24,NULL),(30,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:53',6,25,NULL),(31,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:54',6,26,NULL),(32,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:54',6,27,NULL),(33,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:54',6,28,NULL),(34,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:54',6,29,NULL),(35,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:54',6,30,NULL),(36,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:54',6,32,NULL),(37,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:54',6,31,NULL),(38,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:54',6,34,NULL),(39,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:54',6,33,NULL),(40,'CREATION','Document \'Test\' uploadé','2026-03-10 19:03:55',6,35,NULL),(41,'CREATION','Document \'Test\' uploadé','2026-03-10 19:08:27',6,36,NULL),(42,'CREATION','Document \'Test\' uploadé','2026-03-11 08:58:24',6,37,NULL),(43,'CREATION','Document \'Test\' uploadé','2026-03-11 10:51:07',6,38,NULL),(44,'CREATION','Document \'Test\' uploadé','2026-03-16 16:26:36',6,39,NULL),(45,'CREATION','Document \'Test\' uploadé','2026-03-16 16:26:43',6,40,NULL),(46,'CREATION','Document \'Test\' uploadé','2026-03-16 16:26:49',6,41,NULL),(47,'CREATION','Document \'Test\' uploadé','2026-03-16 16:26:57',6,42,NULL),(48,'CREATION','Document \'Test\' uploadé','2026-03-16 16:27:01',6,43,NULL),(49,'CREATION','Document \'Test\' uploadé','2026-03-16 16:27:04',6,44,NULL),(50,'CREATION','Document \'Test après connexion\' uploadé','2026-03-18 10:15:16',6,45,NULL),(51,'CREATION','Document \'Document créé hors-ligne\' uploadé','2026-03-18 11:22:48',6,46,NULL);
/*!40000 ALTER TABLE `logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `niveaux_validation`
--

DROP TABLE IF EXISTS `niveaux_validation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `niveaux_validation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `entreprise_id` int(11) NOT NULL,
  `nom_niveau` varchar(50) NOT NULL,
  `ordre` int(11) NOT NULL,
  `role_requis` enum('admin_global','admin_pme','manager','employe') NOT NULL,
  `delai_heures` int(11) DEFAULT 48,
  PRIMARY KEY (`id`),
  KEY `entreprise_id` (`entreprise_id`),
  CONSTRAINT `niveaux_validation_ibfk_1` FOREIGN KEY (`entreprise_id`) REFERENCES `entreprises` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `niveaux_validation`
--

LOCK TABLES `niveaux_validation` WRITE;
/*!40000 ALTER TABLE `niveaux_validation` DISABLE KEYS */;
INSERT INTO `niveaux_validation` VALUES (7,1,'Chef d\'équipe',1,'employe',24),(8,1,'Manager',2,'admin_pme',48),(9,1,'Direction',3,'admin_global',48);
/*!40000 ALTER TABLE `niveaux_validation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin_global','admin_pme','employe') NOT NULL DEFAULT 'employe',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `entreprise_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `entreprise_id` (`entreprise_id`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`entreprise_id`) REFERENCES `entreprises` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Armel','armel@mail.com','scrypt:32768:8:1$Pgpipo297yUB9vro$f187b37b7bc700d4e749c69cd11668150d320f4e1f99e4d5e5c7d449a9827f3d450e93153faad1353e23636217c24610203524e64ee69de28c1b04c65975f77c','employe','2026-03-04 10:38:20',NULL),(2,'Super Admin','super@admin.com','scrypt:32768:8:1$RC6OjxpUB9RUSaMy$27ffcf86c4ff84f30d29480d4d3e6eeb7d68ac66065f97f767e8838eba93e6228795541c7421a6176cd622389e66ac803992c979192848e68ba61b9a95ab4b5f','admin_global','2026-03-04 16:17:16',NULL),(3,'Chef Entreprise','chef@pme.com','scrypt:32768:8:1$PsxPEgnmdi7iu2xk$ff2b6bc3ed8b281701577929739c30c55fac668b1bf830aadec4309918f90a6ad37897d1dcd67a0ef9d5e357ed3bffac2c2573e157e0e837d78952617897cf39','admin_pme','2026-03-04 16:17:28',NULL),(4,'Jean Employe','jean@entreprise.com','scrypt:32768:8:1$mLwH4WQSa8dubQuc$2c2ab1d8b684204c948a10f0167435de4547adac5cc217ab3f000367a3f0cda277f468f11e58685ac3b5faff076cc470d21a771615995d07cab606b62c77e5cf','employe','2026-03-04 16:17:38',NULL),(5,'Test','test@test.com','scrypt:32768:8:1$50dZyOpGigJHLOsx$c7b2576df5ab6bf2301680f359202a2527198816949bd30e65fe1d1f4bddf3347a34f9c6c2d429dab57aa3e705d34a4bf8c01c3af7111b320a785ad04519de0b','employe','2026-03-05 19:47:13',NULL),(6,'Super Admin','admin@test.com','scrypt:32768:8:1$u1Y8Vukti1znBR4S$08958e96da897006eb2408591dbdb2d45c545e02516ccbde1ef5d3e2d34fb46447c96c128fc65d7b251c6c1a95555a7827fe2c4c48472424081ca32b3887959c','admin_global','2026-03-09 16:32:53',1),(7,'Chef Equipe','chef@test.com','scrypt:32768:8:1$sOn90DLnoKPe6E0e$0c70d5628190833304e5a72797801dc090eb96fc4809f9baa19d6d96bc3b682cea250cc2bcf3a7cca7bbaf3d550db550542824d296c948f7a53d209fbe6941f3','employe','2026-03-09 20:46:33',NULL),(8,'Manager','manager@test.com','scrypt:32768:8:1$LWgciB9AH8eEk4Mt$cc4d95546301e774ba6f55a6d132372f2c1c4ac1baac6ec77a3baa107f5604cd5ffd255ad3e6725fcb408681135d571247edf521d24fa92cf03aeba3c6acf9b5','admin_pme','2026-03-09 20:49:11',NULL);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `validations_document`
--

DROP TABLE IF EXISTS `validations_document`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `validations_document` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `document_id` int(11) NOT NULL,
  `niveau_id` int(11) NOT NULL,
  `validateur_id` int(11) DEFAULT NULL,
  `statut` enum('en_attente','valide','rejete') DEFAULT 'en_attente',
  `date_action` datetime DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `document_id` (`document_id`),
  KEY `niveau_id` (`niveau_id`),
  KEY `validateur_id` (`validateur_id`),
  CONSTRAINT `validations_document_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE CASCADE,
  CONSTRAINT `validations_document_ibfk_2` FOREIGN KEY (`niveau_id`) REFERENCES `niveaux_validation` (`id`) ON DELETE CASCADE,
  CONSTRAINT `validations_document_ibfk_3` FOREIGN KEY (`validateur_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `validations_document`
--

LOCK TABLES `validations_document` WRITE;
/*!40000 ALTER TABLE `validations_document` DISABLE KEYS */;
INSERT INTO `validations_document` VALUES (1,15,7,7,'valide','2026-03-09 21:48:24','Validé par le chef d\'équipe'),(2,15,8,8,'valide','2026-03-09 21:52:56','Validé par le manager'),(3,15,9,6,'valide','2026-03-09 21:53:49','Approuvé par la direction');
/*!40000 ALTER TABLE `validations_document` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-18 12:45:10
