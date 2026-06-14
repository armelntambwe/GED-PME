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
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('1eb232baef70');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
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
  `entreprise_id` int(11) DEFAULT NULL,
  `categorie_id` int(11) DEFAULT NULL,
  `validateur_id` int(11) DEFAULT NULL,
  `date_validation` datetime DEFAULT NULL,
  `commentaire_rejet` text DEFAULT NULL,
  `niveau_validation_actuel` int(11) DEFAULT 1,
  `workflow_termine` tinyint(1) DEFAULT 0,
  `supprime_le` datetime DEFAULT NULL,
  `supprime_par` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `auteur_id` (`auteur_id`),
  KEY `entreprise_id` (`entreprise_id`),
  CONSTRAINT `documents_ibfk_1` FOREIGN KEY (`auteur_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `documents_ibfk_2` FOREIGN KEY (`entreprise_id`) REFERENCES `entreprises` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=54 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `documents`
--

LOCK TABLES `documents` WRITE;
/*!40000 ALTER TABLE `documents` DISABLE KEYS */;
INSERT INTO `documents` VALUES (1,'Facture Decembre','Facture fournisseur',NULL,NULL,NULL,NULL,'2026-03-04 17:25:16','valide',1,NULL,NULL,1,'2026-03-04 17:39:04',NULL,1,0,NULL,NULL),(2,'Facture Janvier','Facture client A',NULL,NULL,NULL,NULL,'2026-03-04 17:27:07','rejete',3,NULL,NULL,1,NULL,'Signature manquante',1,0,NULL,NULL),(3,'Rapport mensuel','Rapport janvier 2024',NULL,NULL,NULL,NULL,'2026-03-04 17:27:08','valide',3,NULL,NULL,4,'2026-03-04 17:39:59',NULL,1,0,NULL,NULL),(4,'Contrat Client B','Contrat de service',NULL,NULL,NULL,NULL,'2026-03-04 17:27:12','brouillon',3,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(5,'Test cycle','Document test',NULL,NULL,NULL,NULL,'2026-03-04 17:42:26','valide',3,NULL,NULL,1,'2026-03-04 17:42:27',NULL,1,0,NULL,NULL),(6,'Document test avec JWT','',NULL,NULL,NULL,NULL,'2026-03-05 21:42:26','rejete',5,NULL,NULL,11,NULL,'document incomplet',1,0,NULL,NULL),(8,'Document PDF test','Test avec vrai PDF','1.3. Procedures et Fonctions.pdf','uploads\\5_1772915699_1.3._Procedures_et_Fonctions.pdf',694571,'application/pdf','2026-03-07 21:34:59','brouillon',5,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(9,'Document avec log','','test.txt','uploads\\6_1773081922_test.txt',46,'text/plain','2026-03-09 19:45:22','rejete',6,NULL,NULL,11,NULL,'incohérence ',1,0,NULL,NULL),(10,'Document avec log','','test.txt','uploads\\6_1773081998_test.txt',20,'text/plain','2026-03-09 19:46:39','rejete',6,NULL,NULL,6,NULL,'Document incomplet, veuillez recommencer',1,0,NULL,NULL),(11,'Document avec log','','test.txt','uploads\\6_1773082121_test.txt',46,'text/plain','2026-03-09 19:48:41','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(12,'Document pour test rejet','','test.txt','uploads\\6_1773082747_test.txt',46,'text/plain','2026-03-09 19:59:07','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(13,'Document workflow test','','test.txt','uploads\\6_1773086976_test.txt',46,'text/plain','2026-03-09 21:09:36','soumis',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(14,'Document workflow test 2','','test.txt','uploads\\6_1773087359_test.txt',46,'text/plain','2026-03-09 21:15:59','soumis',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(15,'Document workflow test 2','','test.txt','uploads\\6_1773087409_test.txt',46,'text/plain','2026-03-09 21:16:49','valide',6,NULL,NULL,NULL,NULL,NULL,3,1,NULL,NULL),(16,'Test workflow final','','test.txt','uploads\\6_1773088747_test.txt',46,'text/plain','2026-03-09 21:39:07','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(17,'Test','','test.txt','uploads\\6_1773165826_test.txt',4,'text/plain','2026-03-10 19:03:49','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(18,'Test','','test.txt','uploads\\6_1773165826_test.txt',4,'text/plain','2026-03-10 19:03:49','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(19,'Test','','test.txt','uploads\\6_1773165825_test.txt',4,'text/plain','2026-03-10 19:03:49','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(20,'Test','','test.txt','uploads\\6_1773165826_test.txt',4,'text/plain','2026-03-10 19:03:49','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(21,'Test','','test.txt','uploads\\6_1773165825_test.txt',4,'text/plain','2026-03-10 19:03:49','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(22,'Test','','test.txt','uploads\\6_1773165826_test.txt',4,'text/plain','2026-03-10 19:03:49','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(23,'Test','','test.txt','uploads\\6_1773165830_test.txt',4,'text/plain','2026-03-10 19:03:51','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(24,'Test','','test.txt','uploads\\6_1773165831_test.txt',4,'text/plain','2026-03-10 19:03:53','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(25,'Test','','test.txt','uploads\\6_1773165833_test.txt',4,'text/plain','2026-03-10 19:03:53','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(26,'Test','','test.txt','uploads\\6_1773165833_test.txt',4,'text/plain','2026-03-10 19:03:53','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(27,'Test','','test.txt','uploads\\6_1773165833_test.txt',4,'text/plain','2026-03-10 19:03:53','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(28,'Test','','test.txt','uploads\\6_1773165833_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(29,'Test','','test.txt','uploads\\6_1773165834_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(30,'Test','','test.txt','uploads\\6_1773165834_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(31,'Test','','test.txt','uploads\\6_1773165834_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(32,'Test','','test.txt','uploads\\6_1773165834_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(33,'Test','','test.txt','uploads\\6_1773165834_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(34,'Test','','test.txt','uploads\\6_1773165834_test.txt',4,'text/plain','2026-03-10 19:03:54','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(35,'Test','','test.txt','uploads\\6_1773165835_test.txt',4,'text/plain','2026-03-10 19:03:55','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(36,'Test','','test.txt','uploads\\6_1773166107_test.txt',4,'text/plain','2026-03-10 19:08:27','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(37,'Test','','test.txt','uploads\\6_1773215904_test.txt',4,'text/plain','2026-03-11 08:58:24','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(38,'Test','','test.txt','uploads\\6_1773222667_test.txt',4,'text/plain','2026-03-11 10:51:07','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(39,'Test','','test.txt','uploads\\6_1773674794_test.txt',4,'text/plain','2026-03-16 16:26:34','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(40,'Test','','test.txt','uploads\\6_1773674803_test.txt',4,'text/plain','2026-03-16 16:26:43','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(41,'Test','','test.txt','uploads\\6_1773674809_test.txt',4,'text/plain','2026-03-16 16:26:49','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(42,'Test','','test.txt','uploads\\6_1773674817_test.txt',4,'text/plain','2026-03-16 16:26:57','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(43,'Test','','test.txt','uploads\\6_1773674821_test.txt',4,'text/plain','2026-03-16 16:27:01','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(44,'Test','','test.txt','uploads\\6_1773674824_test.txt',4,'text/plain','2026-03-16 16:27:04','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(45,'Test après connexion','','nouveau_test.txt','uploads\\6_1773825315_nouveau_test.txt',38,'text/plain','2026-03-18 10:15:15','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(46,'Document créé hors-ligne','','test_offline.txt','uploads\\6_1773829366_test_offline.txt',38,'text/plain','2026-03-18 11:22:48','brouillon',6,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(47,'audit','sgcbdncdkclsplsjhvgs','TP01_Audit_Informatique.pdf','uploads\\10_1775033281_TP01_Audit_Informatique.pdf',473391,'application/pdf','2026-04-01 09:48:01','valide',10,NULL,0,11,'2026-04-01 10:25:18',NULL,1,0,NULL,NULL),(48,'projet GED ','FSAFCGVDHJADJKLLNBHGCS','Projet GED.pdf','uploads\\10_1775033911_Projet_GED.pdf',302217,'application/pdf','2026-04-01 09:58:31','brouillon',10,NULL,0,NULL,NULL,NULL,1,0,NULL,NULL),(49,'projet GED ','FSAFCGVDHJADJKLLNBHGCS','Projet GED.pdf','uploads\\10_1775033981_Projet_GED.pdf',302217,'application/pdf','2026-04-01 09:59:41','brouillon',10,NULL,0,NULL,NULL,NULL,1,0,NULL,NULL),(50,'texte ged','études des cas','news.txt','uploads\\3_1777390014_news.txt',31954,'text/plain','2026-04-28 16:26:54','brouillon',3,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(51,'texte ged1','','PROJET[1].docx','uploads\\3_1777407456_PROJET1.docx',423013,'application/vnd.openxmlformats-officedocument.wordprocessingml.document','2026-04-28 21:17:36','brouillon',3,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(52,'projet unh','','PROJET[1].docx','uploads\\3_1777501844_PROJET1.docx',423013,'application/vnd.openxmlformats-officedocument.wordprocessingml.document','2026-04-29 23:30:44','brouillon',3,2,NULL,NULL,NULL,NULL,1,0,NULL,NULL),(53,'kin marché','affiche ','850b2b02191ba7b3522b5fdba7a75490.jpg','uploads\\3_1777501893_850b2b02191ba7b3522b5fdba7a75490.jpg',25698,'image/jpeg','2026-04-29 23:31:33','brouillon',3,2,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
/*!40000 ALTER TABLE `documents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `droits_utilisateur`
--

DROP TABLE IF EXISTS `droits_utilisateur`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `droits_utilisateur` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `droit_lecture` tinyint(1) DEFAULT 1,
  `droit_creation` tinyint(1) DEFAULT 0,
  `droit_modification` tinyint(1) DEFAULT 0,
  `droit_suppression` tinyint(1) DEFAULT 0,
  `droit_export` tinyint(1) DEFAULT 0,
  `droit_admin` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `droits_utilisateur_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `droits_utilisateur`
--

LOCK TABLES `droits_utilisateur` WRITE;
/*!40000 ALTER TABLE `droits_utilisateur` DISABLE KEYS */;
INSERT INTO `droits_utilisateur` VALUES (1,1,1,1,0,0,0,0),(2,4,1,1,0,0,0,0),(3,5,1,1,0,0,0,0),(4,7,1,1,0,0,0,0),(5,10,1,1,0,0,0,0),(6,13,1,1,0,0,0,0),(7,34,1,1,0,0,0,0),(8,35,1,1,0,0,0,0),(9,36,1,1,0,0,0,0),(10,39,1,1,0,0,0,0),(11,41,1,1,0,0,0,0),(12,42,1,1,0,0,0,0),(13,43,1,1,0,0,0,0),(14,44,1,1,0,0,0,0),(15,45,1,1,0,0,0,0),(16,46,1,1,0,0,0,0),(17,47,1,1,0,0,0,0),(18,48,1,1,0,0,0,0),(19,49,1,1,0,0,0,0);
/*!40000 ALTER TABLE `droits_utilisateur` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entreprises`
--

LOCK TABLES `entreprises` WRITE;
/*!40000 ALTER TABLE `entreprises` DISABLE KEYS */;
INSERT INTO `entreprises` VALUES (1,'Entreprise Test','Kinshasa','+243811111111','contact@test.cd','2026-03-09 20:44:19','suspendu'),(2,'GED-PME l','Kinshasa, RDC','+243123456789','contact@ged-pme.com','2026-04-06 18:50:32','actif'),(3,'GED-PME Global','Kinshasa, RDC','+243123456789','contact@ged-pme.com','2026-04-06 19:01:23','actif'),(4,'GED-PME Global','Kinshasa, RDC','+243123456789','contact@ged-pme.com','2026-04-06 19:02:08','actif'),(5,'ITM','kasavubu','0994567891','armelntambwe9@gmail.com','2026-04-06 20:27:43','actif'),(6,' Polyclinique  jourdain','Lubumbashi','+2439781467','JOURDAIN@gmail.com','2026-04-10 19:53:41','suspendu'),(7,'Just_Smile','','+243 999920847','Just_Smile@ged-pme.com','2026-04-14 09:54:51','actif'),(8,'Just_Smile1',NULL,'+243 999920847','JustSmile@ged-pme.com','2026-04-14 10:35:42','suspendu'),(9,'Test Notification MODIFIEE','Lubumbashi','987654321','modifie@test.com','2026-04-14 11:48:41','actif'),(10,'MK service','Av. Kasavubu','+2438545632154','lita@gmail.com','2026-04-21 10:00:57','actif'),(11,'UNH','kasapa','+2439781462','UNH@gmail.com','2026-04-21 14:15:46','suspendu'),(12,'GED ','KOLWEZI','+2439781462','GED@gmail.com','2026-04-25 14:17:31','suspendu');
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
  `date_action` timestamp NOT NULL DEFAULT current_timestamp(),
  `date` datetime DEFAULT current_timestamp(),
  `user_id` int(11) NOT NULL,
  `document_id` int(11) DEFAULT NULL,
  `adresse_ip` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=70 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `logs`
--

LOCK TABLES `logs` WRITE;
/*!40000 ALTER TABLE `logs` DISABLE KEYS */;
INSERT INTO `logs` VALUES (1,'CREATION','Document \'Document avec log\' uploadé','2026-04-10 18:13:24','2026-03-09 19:45:23',6,9,NULL),(2,'CREATION','Document \'Document avec log\' uploadé','2026-04-10 18:13:24','2026-03-09 19:46:39',6,10,NULL),(3,'CREATION','Document \'Document avec log\' uploadé','2026-04-10 18:13:24','2026-03-09 19:48:41',6,11,NULL),(4,'SOUMISSION','Document 9 soumis','2026-04-10 18:13:24','2026-03-09 19:50:35',6,9,NULL),(5,'TELECHARGEMENT','Document 9 téléchargé','2026-04-10 18:13:24','2026-03-09 19:52:55',6,9,NULL),(6,'CREATION','Document \'Document pour test rejet\' uploadé','2026-04-10 18:13:24','2026-03-09 19:59:07',6,12,NULL),(7,'SOUMISSION','Document 10 soumis','2026-04-10 18:13:24','2026-03-09 19:59:23',6,10,NULL),(8,'REJET','Document 10 rejeté: Document incomplet, veuillez recommencer','2026-04-10 18:13:24','2026-03-09 19:59:39',6,10,NULL),(9,'CONFIG_WORKFLOW','Workflow configuré avec 3 étapes','2026-04-10 18:13:24','2026-03-09 21:06:43',6,NULL,NULL),(10,'CREATION','Document \'Document workflow test\' uploadé','2026-04-10 18:13:24','2026-03-09 21:09:36',6,13,NULL),(11,'SOUMISSION','Document 13 soumis','2026-04-10 18:13:24','2026-03-09 21:10:47',6,13,NULL),(12,'CONFIG_WORKFLOW','Workflow configuré avec 3 étapes','2026-04-10 18:13:24','2026-03-09 21:14:15',6,NULL,NULL),(13,'CONFIG_WORKFLOW','Workflow configuré avec 3 étapes','2026-04-10 18:13:24','2026-03-09 21:14:26',6,NULL,NULL),(14,'CREATION','Document \'Document workflow test 2\' uploadé','2026-04-10 18:13:24','2026-03-09 21:15:59',6,14,NULL),(15,'SOUMISSION','Document 14 soumis','2026-04-10 18:13:24','2026-03-09 21:16:34',6,14,NULL),(16,'CREATION','Document \'Document workflow test 2\' uploadé','2026-04-10 18:13:24','2026-03-09 21:16:49',6,15,NULL),(17,'CREATION','Document \'Test workflow final\' uploadé','2026-04-10 18:13:24','2026-03-09 21:39:07',6,16,NULL),(18,'SOUMISSION','Document 15 soumis','2026-04-10 18:13:24','2026-03-09 21:39:40',6,15,NULL),(19,'VALIDATION_ETAPE','Document 15 - Étape 1/3 validée','2026-04-10 18:13:24','2026-03-09 21:48:24',7,15,NULL),(20,'VALIDATION_ETAPE','Document 15 - Étape 2/3 validée','2026-04-10 18:13:24','2026-03-09 21:52:56',8,15,NULL),(21,'VALIDATION_ETAPE','Document 15 - Étape 3/3 validée','2026-04-10 18:13:24','2026-03-09 21:53:49',6,15,NULL),(22,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:50',6,20,NULL),(23,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:50',6,18,NULL),(24,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:50',6,22,NULL),(25,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:50',6,17,NULL),(26,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:50',6,21,NULL),(27,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:50',6,19,NULL),(28,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:53',6,23,NULL),(29,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:53',6,24,NULL),(30,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:53',6,25,NULL),(31,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:54',6,26,NULL),(32,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:54',6,27,NULL),(33,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:54',6,28,NULL),(34,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:54',6,29,NULL),(35,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:54',6,30,NULL),(36,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:54',6,32,NULL),(37,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:54',6,31,NULL),(38,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:54',6,34,NULL),(39,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:54',6,33,NULL),(40,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:03:55',6,35,NULL),(41,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-10 19:08:27',6,36,NULL),(42,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-11 08:58:24',6,37,NULL),(43,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-11 10:51:07',6,38,NULL),(44,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-16 16:26:36',6,39,NULL),(45,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-16 16:26:43',6,40,NULL),(46,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-16 16:26:49',6,41,NULL),(47,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-16 16:26:57',6,42,NULL),(48,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-16 16:27:01',6,43,NULL),(49,'CREATION','Document \'Test\' uploadé','2026-04-10 18:13:24','2026-03-16 16:27:04',6,44,NULL),(50,'CREATION','Document \'Test après connexion\' uploadé','2026-04-10 18:13:24','2026-03-18 10:15:16',6,45,NULL),(51,'CREATION','Document \'Document créé hors-ligne\' uploadé','2026-04-10 18:13:24','2026-03-18 11:22:48',6,46,NULL),(52,'CONNEXION','Connexion de admin@ged-pme.com','2026-04-13 18:51:25','2026-04-13 19:51:25',33,NULL,NULL),(53,'CREATION_EMPLOYE','Employé \'Jemima\' créé','2026-04-14 13:05:48','2026-04-14 14:05:48',3,NULL,NULL),(54,'RESTAURATION','Document 7 restauré','2026-04-14 13:52:59','2026-04-14 14:52:59',3,7,NULL),(55,'RESTAURATION','Document 7 restauré','2026-04-14 13:56:08','2026-04-14 14:56:08',3,7,NULL),(56,'SUPPRESSION_DEFINITIVE','Document 7 supprimé définitivement','2026-04-14 21:38:20','2026-04-14 22:38:20',3,7,NULL),(57,'CREATION_EMPLOYE','Employé \'HARMONIE BILONDA\' créé','2026-04-27 18:00:45','2026-04-27 19:00:45',3,NULL,NULL),(58,'CREATION_EMPLOYE','Employé \'Granel\' créé','2026-04-27 19:32:46','2026-04-27 20:32:46',3,NULL,NULL),(59,'CREATION_EMPLOYE','Employé \'Test Admin PME\' créé','2026-04-27 19:43:54','2026-04-27 20:43:54',3,NULL,NULL),(60,'CREATION_EMPLOYE','Employé \'mira\' créé','2026-04-27 20:21:47','2026-04-27 21:21:47',3,NULL,NULL),(61,'CREATION_EMPLOYE','Employé \'merveille \' créé','2026-04-27 21:01:35','2026-04-27 22:01:35',3,NULL,NULL),(62,'CREATION_EMPLOYE','Employé \'merveill\' créé','2026-04-28 13:50:25','2026-04-28 14:50:25',3,NULL,NULL),(63,'CREATION_EMPLOYE','Employé \'ARMI\' créé','2026-04-28 14:27:32','2026-04-28 15:27:32',3,NULL,NULL),(64,'CREATION','Document \'texte ged\' uploadé','2026-04-28 15:26:55','2026-04-28 16:26:55',3,50,NULL),(65,'CREATION','Document \'texte ged1\' uploadé','2026-04-28 20:17:36','2026-04-28 21:17:36',3,51,NULL),(66,'CREATION','Document \'projet unh\' uploadé','2026-04-29 22:30:44','2026-04-29 23:30:44',3,52,NULL),(67,'CREATION','Document \'kin marché\' uploadé','2026-04-29 22:31:33','2026-04-29 23:31:33',3,53,NULL),(68,'CREATION_EMPLOYE','Employé \'delly\' créé','2026-04-29 22:43:21','2026-04-29 23:43:21',3,NULL,NULL),(69,'CREATION_EMPLOYE','Employé \'clover bukasa\' créé','2026-04-29 22:58:09','2026-04-29 23:58:09',3,NULL,NULL);
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
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notifications` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `type` varchar(50) NOT NULL,
  `message` text NOT NULL,
  `lien` varchar(255) DEFAULT NULL,
  `lue` tinyint(1) DEFAULT 0,
  `date_creation` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=60 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
INSERT INTO `notifications` VALUES (1,33,'ENTREPRISE_CREEE','✅ L\'entreprise  Polyclinique  jourdain a été créée','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 18:53:41'),(2,33,'ENTREPRISE_MODIFIEE','📝 L\'entreprise  Polyclinique  jourdain a été modifiée','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 18:55:59'),(3,33,'ENTREPRISE_MODIFIEE','📝 L\'entreprise  Polyclinique  jourdain a été modifiée','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 19:18:10'),(4,33,'ENTREPRISE_TOGGLE','🔄 L\'entreprise  Polyclinique  jourdain est maintenant suspendu','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 19:18:15'),(5,33,'ENTREPRISE_TOGGLE','🔄 L\'entreprise  Polyclinique  jourdain est maintenant actif','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 19:18:18'),(6,33,'ENTREPRISE_TOGGLE','🔄 L\'entreprise  Polyclinique  jourdain est maintenant suspendu','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 19:18:21'),(7,33,'ENTREPRISE_TOGGLE','🔄 L\'entreprise Entreprise Test est maintenant suspendu','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 19:18:23'),(8,33,'ENTREPRISE_MODIFIEE','📝 L\'entreprise  Polyclinique  jourdain a été modifiée','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 19:18:27'),(9,33,'ENTREPRISE_TOGGLE','🔄 L\'entreprise  Polyclinique  jourdain est maintenant actif','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 19:20:49'),(10,33,'ENTREPRISE_TOGGLE','🔄 L\'entreprise Entreprise Test est maintenant actif','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 19:20:51'),(11,33,'ENTREPRISE_TOGGLE','🔄 L\'entreprise Entreprise Test est maintenant suspendu','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 19:20:53'),(12,33,'ENTREPRISE_TOGGLE','🔄 L\'entreprise  Polyclinique  jourdain est maintenant suspendu','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 19:41:29'),(13,33,'ENTREPRISE_MODIFIEE','📝 L\'entreprise Entreprise Test a été modifiée','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 20:15:27'),(14,33,'ENTREPRISE_MODIFIEE','📝 L\'entreprise ITM a été modifiée','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 20:15:56'),(15,33,'ENTREPRISE_TOGGLE','🔄 L\'entreprise Entreprise Test est maintenant actif','/dashboard-admin-global?tab=entreprises',1,'2026-04-10 20:59:39'),(16,33,'ENTREPRISE_MODIFIEE','L\'entreprise GED-PME l a été modifiée','/dashboard-admin-global?tab=entreprises',0,'2026-04-14 10:41:29'),(17,33,'ENTREPRISE_CREEE','L\'entreprise Test Notification a été créée','/dashboard-admin-global?tab=entreprises',0,'2026-04-14 10:48:41'),(18,33,'ENTREPRISE_MODIFIEE','L\'entreprise Test Notification MODIFIEE a été modifiée','/dashboard-admin-global?tab=entreprises',1,'2026-04-14 10:50:51'),(19,33,'ENTREPRISE_TOGGLE','L\'entreprise  Polyclinique  jourdain est maintenant suspendu','/dashboard-admin-global?tab=entreprises',0,'2026-04-14 10:59:00'),(20,33,'ENTREPRISE_MODIFIEE','L\'entreprise  Polyclinique  jourdain a été modifiée','/dashboard-admin-global?tab=entreprises',1,'2026-04-14 10:59:13'),(21,33,'ENTREPRISE_TOGGLE','L\'entreprise  Polyclinique  jourdain est maintenant actif','/dashboard-admin-global?tab=entreprises',1,'2026-04-14 10:59:52'),(22,3,'EMPLOYE_CREE','L\'employé Jemima a été créé','/dashboard-pme?tab=employes',0,'2026-04-14 13:05:48'),(23,11,'ENTREPRISE_TOGGLE','L\'entreprise  Polyclinique  jourdain est maintenant suspendu','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 09:32:11'),(24,11,'ENTREPRISE_TOGGLE','L\'entreprise  Polyclinique  jourdain est maintenant actif','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 09:32:15'),(25,11,'ENTREPRISE_TOGGLE','L\'entreprise  Polyclinique  jourdain est maintenant suspendu','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 09:32:16'),(26,11,'ENTREPRISE_TOGGLE','L\'entreprise  Polyclinique  jourdain est maintenant actif','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 09:32:17'),(27,11,'ENTREPRISE_TOGGLE','L\'entreprise Entreprise Test est maintenant suspendu','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 09:32:19'),(28,11,'ENTREPRISE_TOGGLE','L\'entreprise  Polyclinique  jourdain est maintenant suspendu','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 09:32:55'),(29,11,'ENTREPRISE_TOGGLE','L\'entreprise Entreprise Test est maintenant actif','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 09:33:01'),(30,11,'ENTREPRISE_TOGGLE','L\'entreprise Entreprise Test est maintenant suspendu','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 09:33:03'),(31,11,'ENTREPRISE_TOGGLE','L\'entreprise Entreprise Test est maintenant actif','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 09:33:04'),(32,11,'ENTREPRISE_TOGGLE','L\'entreprise Entreprise Test est maintenant suspendu','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 09:33:04'),(33,11,'ENTREPRISE_TOGGLE','L\'entreprise Entreprise Test est maintenant actif','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 09:33:05'),(34,11,'ENTREPRISE_TOGGLE','L\'entreprise Entreprise Test est maintenant suspendu','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 09:33:05'),(35,11,'ENTREPRISE_TOGGLE','L\'entreprise UNH est maintenant actif','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 13:37:18'),(36,11,'ENTREPRISE_TOGGLE','L\'entreprise MK service est maintenant actif','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 13:37:22'),(37,11,'ENTREPRISE_MODIFIEE','L\'entreprise  Polyclinique  jourdain a été modifiée','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 13:37:34'),(38,11,'ENTREPRISE_SUPPRIMEE','L\'entreprise Just_Smile1 a été supprimée (soft delete)','/dashboard-admin-global?tab=entreprises',0,'2026-04-21 14:17:00'),(39,11,'USER_TOGGLE','L\'utilisateur Armel Ntambwe a été désactivé','/dashboard-admin-global?tab=users',0,'2026-04-21 14:17:59'),(40,11,'USER_TOGGLE','L\'utilisateur Jemima a été désactivé','/dashboard-admin-global?tab=users',0,'2026-04-21 14:18:02'),(41,11,'PASSWORD_RESET','Le mot de passe de l\'utilisateur Jean Employe a été réinitialisé','/dashboard-admin-global?tab=users',0,'2026-04-21 14:19:53'),(42,11,'ENTREPRISE_MODIFIEE','L\'entreprise Entreprise Test a été modifiée','/dashboard-admin-global?tab=entreprises',0,'2026-04-22 06:27:11'),(43,11,'ENTREPRISE_TOGGLE','L\'entreprise UNH est maintenant suspendu','/dashboard-admin-global?tab=entreprises',0,'2026-04-22 09:56:17'),(44,11,'ENTREPRISE_TOGGLE','L\'entreprise UNH est maintenant actif','/dashboard-admin-global?tab=entreprises',0,'2026-04-22 09:56:25'),(45,11,'ENTREPRISE_TOGGLE','L\'entreprise UNH est maintenant suspendu','/dashboard-admin-global?tab=entreprises',0,'2026-04-22 09:56:27'),(46,33,'ENTREPRISE_CREEE','L\'entreprise GED  a été créée','/dashboard-admin-global?tab=entreprises',0,'2026-04-25 13:17:31'),(47,33,'USER_TOGGLE','L\'utilisateur Armel Ntambwe a été activé','/dashboard-admin-global?tab=users',0,'2026-04-25 13:18:17'),(48,33,'ENTREPRISE_TOGGLE','L\'entreprise GED  est maintenant suspendu','/dashboard-admin-global?tab=entreprises',0,'2026-04-27 16:39:43'),(49,3,'EMPLOYE_CREE','L\'employé HARMONIE BILONDA a été créé','/dashboard-pme?tab=employes',0,'2026-04-27 18:00:45'),(50,3,'EMPLOYE_CREE','L\'employé Granel a été créé','/dashboard-pme?tab=employes',1,'2026-04-27 19:32:46'),(51,3,'EMPLOYE_CREE','L\'employé Test Admin PME a été créé','/dashboard-pme?tab=employes',0,'2026-04-27 19:43:54'),(52,3,'EMPLOYE_CREE','L\'employé mira a été créé','/dashboard-pme?tab=employes',0,'2026-04-27 20:21:47'),(53,3,'EMPLOYE_CREE','L\'employé merveille  a été créé','/dashboard-pme?tab=employes',0,'2026-04-27 21:01:35'),(54,11,'USER_TOGGLE','L\'utilisateur merveille  a été désactivé','/dashboard-admin-global?tab=users',0,'2026-04-28 13:41:36'),(55,3,'EMPLOYE_CREE','L\'employé merveill a été créé','/dashboard-pme?tab=employes',0,'2026-04-28 13:50:25'),(56,3,'EMPLOYE_CREE','L\'employé ARMI a été créé','/dashboard-pme?tab=employes',0,'2026-04-28 14:27:32'),(57,33,'USER_TOGGLE','L\'utilisateur merveille  a été activé','/dashboard-admin-global?tab=users',0,'2026-04-29 20:00:16'),(58,3,'EMPLOYE_CREE','L\'employé delly a été créé','/dashboard-pme?tab=employes',0,'2026-04-29 22:43:21'),(59,3,'EMPLOYE_CREE','L\'employé clover bukasa a été créé','/dashboard-pme?tab=employes',0,'2026-04-29 22:58:09');
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
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
  `prenom` varchar(100) DEFAULT NULL,
  `nom_famille` varchar(100) DEFAULT NULL,
  `email` varchar(150) NOT NULL,
  `matricule` varchar(50) DEFAULT NULL,
  `departement` varchar(100) DEFAULT NULL,
  `poste` varchar(100) DEFAULT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `type_auth` varchar(20) DEFAULT 'local',
  `type_utilisateur` varchar(20) DEFAULT 'interne',
  `role` enum('admin_global','admin_pme','employe') NOT NULL DEFAULT 'employe',
  `actif` tinyint(1) DEFAULT 1,
  `quota_stockage` int(11) DEFAULT 5120,
  `langue` varchar(10) DEFAULT 'fr',
  `date_inscription` timestamp NOT NULL DEFAULT current_timestamp(),
  `date_derniere_connexion` datetime DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `entreprise_id` int(11) DEFAULT NULL,
  `date_expiration` date DEFAULT NULL,
  `sessions_max` int(11) DEFAULT 2,
  `centre_cout` varchar(50) DEFAULT NULL,
  `metadonnees_defaut` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `entreprise_id` (`entreprise_id`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`entreprise_id`) REFERENCES `entreprises` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Armel',NULL,NULL,'armel@mail.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$Pgpipo297yUB9vro$f187b37b7bc700d4e749c69cd11668150d320f4e1f99e4d5e5c7d449a9827f3d450e93153faad1353e23636217c24610203524e64ee69de28c1b04c65975f77c','local','interne','employe',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-03-04 10:38:20',2,NULL,2,NULL,NULL),(2,'Super Admin',NULL,NULL,'super@admin.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$RC6OjxpUB9RUSaMy$27ffcf86c4ff84f30d29480d4d3e6eeb7d68ac66065f97f767e8838eba93e6228795541c7421a6176cd622389e66ac803992c979192848e68ba61b9a95ab4b5f','local','interne','admin_global',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-03-04 16:17:16',NULL,NULL,2,NULL,NULL),(3,'Chef Entreprise',NULL,NULL,'chef@pme.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$PsxPEgnmdi7iu2xk$ff2b6bc3ed8b281701577929739c30c55fac668b1bf830aadec4309918f90a6ad37897d1dcd67a0ef9d5e357ed3bffac2c2573e157e0e837d78952617897cf39','local','interne','admin_pme',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-03-04 16:17:28',2,NULL,2,NULL,NULL),(4,'Jean Employe',NULL,NULL,'jean@entreprise.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$eup2Ban9TY1N5RlJ$b2260393fabc649690eeac1febf0c31a2dff21279fab7186a524df1c64c243dfa7cc80a52ebaecce79a8f0fe8f6c6b0823d6db728ae8b37773d4a9e2fff53654','local','interne','employe',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-03-04 16:17:38',2,NULL,2,NULL,NULL),(5,'Test',NULL,NULL,'test@test.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$50dZyOpGigJHLOsx$c7b2576df5ab6bf2301680f359202a2527198816949bd30e65fe1d1f4bddf3347a34f9c6c2d429dab57aa3e705d34a4bf8c01c3af7111b320a785ad04519de0b','local','interne','employe',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-03-05 19:47:13',2,NULL,2,NULL,NULL),(6,'Super Admin',NULL,NULL,'admin@test.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$RANDOM$hash','local','interne','admin_global',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-03-09 16:32:53',1,NULL,2,NULL,NULL),(7,'Chef Equipe',NULL,NULL,'chef@test.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$sOn90DLnoKPe6E0e$0c70d5628190833304e5a72797801dc090eb96fc4809f9baa19d6d96bc3b682cea250cc2bcf3a7cca7bbaf3d550db550542824d296c948f7a53d209fbe6941f3','local','interne','employe',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-03-09 20:46:33',2,NULL,2,NULL,NULL),(8,'Manager',NULL,NULL,'manager@test.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$LWgciB9AH8eEk4Mt$cc4d95546301e774ba6f55a6d132372f2c1c4ac1baac6ec77a3baa107f5604cd5ffd255ad3e6725fcb408681135d571247edf521d24fa92cf03aeba3c6acf9b5','local','interne','admin_pme',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-03-09 20:49:11',2,NULL,2,NULL,NULL),(10,'Ruth',NULL,NULL,'ruth@test.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$MOuW9PENtCxSuTjG$5305db92a8751877caae39d996c161d2491cf0b7fda8c26dcf27b234df264f5a3608562e7847cc6dc57290cce4cd08c454f171c2ce702a1e2476711a7ec6eec7','local','interne','employe',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-03-31 22:12:22',2,NULL,2,NULL,NULL),(11,'Nouvel Admin',NULL,NULL,'newadmin@test.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$S1X9tUz5LOBbR2M6$3ae2ec7eacf70079f8b063bb73f56deaa5d8f5b85cb47656153975330c31af958d202e86511c4e5ebb0585e908a3cf592000a242818bfaf023bd394b8c78e4f5','local','interne','admin_global',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-04-01 09:12:51',NULL,NULL,2,NULL,NULL),(12,'Plamedi',NULL,NULL,'plamedi@pme.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$S1X9tUz5LOBbR2M6$3ae2ec7eacf70079f8b063bb73f56deaa5d8f5b85cb47656153975330c31af958d202e86511c4e5ebb0585e908a3cf592000a242818bfaf023bd394b8c78e4f5','local','interne','admin_pme',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-04-01 20:44:26',1,NULL,2,NULL,NULL),(13,'plamedie',NULL,NULL,'plamedie@gmail.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$O9IbmA5BCQN5Y9ZR$507c1677e9241d65b6286e005bfcf450ee9a70ae3cb34cc51bc062f73afe8836534f0d73470fcf447f09999948932d67bc544e2dec9d2f5749ed740222e578d2','local','interne','employe',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-04-01 21:02:02',2,NULL,2,NULL,NULL),(33,'Administrateur Global',NULL,NULL,'admin@ged-pme.com',NULL,NULL,NULL,NULL,'scrypt:32768:8:1$jDHF3TPUASSNiZQM$9f5e380612e935e2090a0b4c8931e6c5230c99265eebf0e69ccb64de0ebbd9150038d54086c7f66be454d11d6441db9ef95d5b8031478250e7ed8851a8c575e9','local','interne','admin_global',1,5120,'fr','2026-04-10 18:14:54',NULL,'2026-04-06 18:12:48',1,NULL,2,NULL,NULL),(34,'Jordan',NULL,NULL,'Jordan@gmail.com',NULL,NULL,NULL,'+2439988455','scrypt:32768:8:1$iPDGM0n56PWE11Jm$2a0857433cec34675ccb534baccc0eaae176337f190e7d8551a5240aa02eb4f2e28a84edbfb6d03a5ae5e688151df46797a2b4cec1dfec67aa56d407865d6a28','local','interne','employe',1,5120,'fr','2026-04-10 21:39:32',NULL,'2026-04-10 21:39:32',2,NULL,2,NULL,NULL),(35,'ARMIE ',NULL,NULL,'armi@gmail.com',NULL,NULL,NULL,'+2439988455','scrypt:32768:8:1$gL6LpKubvvi4XoPC$19707ccc331dbe68542be3fe8a327b663aba841cbbed19625fc22b9a164f97fd588cf5baf7da7a425b1d635405b18064013c3bd1d19a3b332c6c1ae5a9da0038','local','interne','employe',1,5120,'fr','2026-04-10 21:58:52',NULL,'2026-04-10 21:58:52',2,NULL,2,NULL,NULL),(36,'Test User',NULL,NULL,'test_1775858470030@test.com',NULL,NULL,NULL,'123456789','scrypt:32768:8:1$9kihj27yOz5y6Jnh$12f1b71ccd5507f14a9ffb24270bc5e551cf45ea4b412b731e45b30102b84c87961ec4ba622699284a0427d1a1c9707bcafba756e09b9534d1b033849a37ee32','local','interne','employe',1,5120,'fr','2026-04-10 22:01:10',NULL,'2026-04-10 22:01:10',2,NULL,2,NULL,NULL),(37,'ARMEL',NULL,NULL,'Just_Smile@ged-pme.com',NULL,NULL,NULL,'+243 999920847','scrypt:32768:8:1$05dlEvCWkyI1zb9s$d0777d5d0c16a3147008a276b51578d0641404a357dc6823e44d0b7b26792f5b589a231d7f1f20c4e71a39cfeb012056e857be564cf7409e523daa58006977c7','local','interne','admin_pme',1,5120,'fr','2026-04-14 08:54:51',NULL,'2026-04-14 08:54:51',7,NULL,2,NULL,NULL),(38,'Ntambwe',NULL,NULL,'JustSmile@ged-pme.com',NULL,NULL,NULL,'+243 999920847','scrypt:32768:8:1$zI27fUWYSH5zkYV3$d279f188fd562299c4ee774eaefce39834ec7b4034747a3f859fbedd0350766339d829edd3e23c9a811a0eeb6ea43d0057027df7f2f5fa89ebd5bd5475ced1fd','local','interne','admin_pme',1,5120,'fr','2026-04-14 09:35:42',NULL,'2026-04-14 09:35:42',8,NULL,2,NULL,NULL),(39,'Jemima',NULL,NULL,'Jemima@gmail.com',NULL,NULL,NULL,'+2439988455','scrypt:32768:8:1$XAEXR4GcuQ3L4r5k$d433df7a7b0ad1ea2e6704b1ac76670f2c543a42f95f5bcccab079101ce0f4929b829f15bb857e65a3c9d28f97e83450977a176822cf2aa21ff2b0c51fa52bbe','local','interne','employe',0,5120,'fr','2026-04-14 13:05:48',NULL,'2026-04-14 13:05:48',2,NULL,2,NULL,NULL),(40,'Armel Ntambwe',NULL,NULL,'armel@gmail.com',NULL,NULL,NULL,'+2439988455','scrypt:32768:8:1$eGbIsoMkTk1OBBMF$91ca3972586b8ba6084e6ba276fcc52eb3b0dba63cdd6d443a967ee067a2b7752fa7dee9296b99a6627d6541fddb02257a7726dab0b2322579c5f13a77d37207','local','interne','admin_pme',1,5120,'fr','2026-04-21 09:00:57',NULL,'2026-04-21 09:00:57',10,NULL,2,NULL,NULL),(41,'HARMONIE BILONDA',NULL,NULL,'harmonie@gmail.com',NULL,NULL,NULL,'+24399884521','scrypt:32768:8:1$IbaZM72u2IdZ49DT$56e4f217e5e17921043f2441fe630fb07ce2e05ff83de9c6d06bc7a213019b41d0ca4d06fe55fb3f597a6abfcf9e387d75f91607896e6b834fbaed80287d2f6e','local','interne','employe',1,5120,'fr','2026-04-27 18:00:45',NULL,'2026-04-27 18:00:45',2,NULL,2,NULL,NULL),(42,'Granel',NULL,NULL,'granel@gmail.com',NULL,NULL,NULL,'+24399884521','scrypt:32768:8:1$jUXnHRlwRX6qFuJs$a912bf261407e6c56999eac5166e3e77f161e4f82022f5080d3ecf83fdebc39a1955314bce7ba4bfe0d70070a8d930d20c8d37934b47f70a6f56c11df1f1b4e0','local','interne','employe',1,5120,'fr','2026-04-27 19:32:46',NULL,'2026-04-27 19:32:46',2,NULL,2,NULL,NULL),(43,'Test Admin PME',NULL,NULL,'test_1777319033899@pme.com',NULL,NULL,NULL,'123456789','scrypt:32768:8:1$7qBDiItuZGMHE0eY$884b8b6341add0d40b6f5082f7f577fca07e45065b571b3bacbe73c7ac046a0334e573dfcbf2d71d0676f7f32ba9858a0e1c4cd2657dc48c8d7490f7832f996b','local','interne','employe',1,5120,'fr','2026-04-27 19:43:54',NULL,'2026-04-27 19:43:54',2,NULL,2,NULL,NULL),(44,'mira',NULL,NULL,'mira @gmail.com',NULL,NULL,NULL,'+24399884521','scrypt:32768:8:1$3M6Hou7rxBadbhKv$994927bdd7af70ce437890859c0f5dab24dad2b263d235477e633289c8efcbf54cf9dee01dc9f938f7db213dd36f0917114fdfb577bc007cbc9297f29e0b74d0','local','interne','employe',1,5120,'fr','2026-04-27 20:21:47',NULL,'2026-04-27 20:21:47',2,NULL,2,NULL,NULL),(45,'merveille ',NULL,NULL,'merveille @gmail.com',NULL,NULL,NULL,'+2439781462','scrypt:32768:8:1$jElaqtytRiYkbhD0$0bc4efd46f47e9b7476e8441a92a7d05c2f55aafe6bdf912114e64d6338f7e0e58712bb8855d410d2bfab1d8328af6cd54af08ab179acf86f353356471009229','local','interne','employe',1,5120,'fr','2026-04-27 21:01:35',NULL,'2026-04-27 21:01:35',2,NULL,2,NULL,NULL),(46,'merveill',NULL,NULL,'merveill @gmail.com',NULL,NULL,NULL,'+2439781460','scrypt:32768:8:1$3Mv7tk3afupTF82M$ae2e73b0f9eb9d13d5247a0ffa3fe35da9cb338e4db75d689f01f28e287943f6236c415df2315c950746c3eaf29179a1d05e4a22a8cc71ed03c14bc227f5eeb7','local','interne','employe',1,5120,'fr','2026-04-28 13:50:25',NULL,'2026-04-28 13:50:25',2,NULL,2,NULL,NULL),(47,'ARMI',NULL,NULL,'ARMI@pme.com',NULL,NULL,NULL,'+2439781462','scrypt:32768:8:1$J7TWHV0QhKTenmR9$a7744e2c6c81ab9f89002d7ae0c9380717e9b96559bd96c69eb28744aac346126a09ca60839c2dbbe30bdaf3deb467324ae22dfbd2e61605d560772bf170426e','local','interne','employe',1,5120,'fr','2026-04-28 14:27:32',NULL,'2026-04-28 14:27:32',2,NULL,2,NULL,NULL),(48,'delly',NULL,NULL,'delly@gmail.com',NULL,NULL,NULL,'+2439988488','scrypt:32768:8:1$jKZ3ada3CyP8G36g$cf35076d2e222687e94b81b8aa512383aa0b3b4a05af91ff393cdbfc1edc386eafa5934edf09e156781b8e2871d66258a6038c8eb969e18acf465b84eaff1da3','local','interne','employe',1,5120,'fr','2026-04-29 22:43:21',NULL,'2026-04-29 22:43:21',2,NULL,2,NULL,NULL),(49,'clover bukasa',NULL,NULL,'cloverbukasa@gmail.com',NULL,NULL,NULL,'+2439984569','scrypt:32768:8:1$SoMIpywsDh5TIeio$f3b944cf75697fe361f7936fb903ea38e431ec99d1bfae021ac4c6d027681aa89780d64a561fe39952668d5f498fb8a3101d2d45851f198f38a063411fcf7672','local','interne','employe',1,5120,'fr','2026-04-29 22:58:09',NULL,'2026-04-29 22:58:09',2,NULL,2,NULL,NULL),(50,'Test Admin',NULL,NULL,'test@pme.com',NULL,NULL,NULL,NULL,'pbkdf2:sha256:260000$123456$abcdef123456','local','interne','admin_pme',1,5120,'fr','2026-05-21 07:55:54',NULL,'2026-05-21 07:55:54',2,NULL,2,NULL,NULL);
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

-- Dump completed on 2026-05-30  6:23:22
