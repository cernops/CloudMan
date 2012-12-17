-- MySQL dump 10.13  Distrib 5.1.61, for koji-linux-gnu (x86_64)
--
-- Host: localhost    Database: malik
-- ------------------------------------------------------
-- Server version	5.1.61

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `changelog`
--

DROP TABLE IF EXISTS `changelog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `changelog` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `category` varchar(100) NOT NULL,
  `name` varchar(100) NOT NULL,
  `operation` varchar(100) NOT NULL,
  `comment` varchar(1000) DEFAULT NULL,
  `sys_comment` varchar(1000) DEFAULT NULL,
  `user` varchar(100) NOT NULL,
  `datetime` datetime NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT '1',
  `object_id` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9311 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `changelog`
--

LOCK TABLES `changelog` WRITE;
/*!40000 ALTER TABLE `changelog` DISABLE KEYS */;
/*!40000 ALTER TABLE `changelog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `egroups`
--

DROP TABLE IF EXISTS `egroups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `egroups` (
  `name` varchar(40) NOT NULL,
  `status` tinyint(1) DEFAULT '1',
  `empty` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `egroups`
--

LOCK TABLES `egroups` WRITE;
/*!40000 ALTER TABLE `egroups` DISABLE KEYS */;
/*!40000 ALTER TABLE `egroups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `group_allocation`
--

DROP TABLE IF EXISTS `group_allocation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `group_allocation` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `group_id` int(10) unsigned NOT NULL,
  `project_allocation_id` int(10) unsigned DEFAULT NULL,
  `parent_group_allocation_id` int(10) unsigned DEFAULT NULL,
  `hepspec` float unsigned DEFAULT NULL,
  `memory` float unsigned DEFAULT NULL,
  `storage` float unsigned DEFAULT NULL,
  `bandwidth` float unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_group_allocation` (`name`),
  KEY `fk_group_group_allocation` (`group_id`),
  KEY `fk_project_group_allocation` (`project_allocation_id`),
  KEY `fk_parent_group_group_allocation` (`parent_group_allocation_id`),
  CONSTRAINT `fk_group_group_allocation` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_parent_group_group_allocation` FOREIGN KEY (`parent_group_allocation_id`) REFERENCES `group_allocation` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_project_group_allocation` FOREIGN KEY (`project_allocation_id`) REFERENCES `project_allocation` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9278 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_allocation`
--

LOCK TABLES `group_allocation` WRITE;
/*!40000 ALTER TABLE `group_allocation` DISABLE KEYS */;
/*!40000 ALTER TABLE `group_allocation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `group_allocation_allowed_resource_type`
--

DROP TABLE IF EXISTS `group_allocation_allowed_resource_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `group_allocation_allowed_resource_type` (
  `group_allocation_id` int(10) unsigned NOT NULL,
  `resource_type_id` smallint(5) unsigned NOT NULL,
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`group_allocation_id`,`resource_type_id`),
  UNIQUE KEY `id` (`id`),
  KEY `fk_resource_group_allocation_allowed_resource_type` (`resource_type_id`),
  CONSTRAINT `fk_group_group_allocation_allowed_resource_type` FOREIGN KEY (`group_allocation_id`) REFERENCES `group_allocation` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_resource_group_allocation_allowed_resource_type` FOREIGN KEY (`resource_type_id`) REFERENCES `resource_type` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8777 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_allocation_allowed_resource_type`
--

LOCK TABLES `group_allocation_allowed_resource_type` WRITE;
/*!40000 ALTER TABLE `group_allocation_allowed_resource_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `group_allocation_allowed_resource_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `group_allocation_metadata`
--

DROP TABLE IF EXISTS `group_allocation_metadata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `group_allocation_metadata` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_allocation_id` int(11) NOT NULL,
  `attribute` varchar(100) DEFAULT NULL,
  `value` varchar(5000) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `group_allocation_id_refs_id_94bde5fa` (`group_allocation_id`)
) ENGINE=InnoDB AUTO_INCREMENT=15024 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_allocation_metadata`
--

LOCK TABLES `group_allocation_metadata` WRITE;
/*!40000 ALTER TABLE `group_allocation_metadata` DISABLE KEYS */;
/*!40000 ALTER TABLE `group_allocation_metadata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(100) DEFAULT NULL,
  `admin_group` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_zone` (`name`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1590 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `groups`
--

LOCK TABLES `groups` WRITE;
/*!40000 ALTER TABLE `groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project`
--

DROP TABLE IF EXISTS `project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(100) DEFAULT NULL,
  `admin_group` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_project` (`name`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=247 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project`
--

LOCK TABLES `project` WRITE;
/*!40000 ALTER TABLE `project` DISABLE KEYS */;
/*!40000 ALTER TABLE `project` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project_allocation`
--

DROP TABLE IF EXISTS `project_allocation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_allocation` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `top_level_allocation_id` int(10) unsigned NOT NULL,
  `project_id` int(10) unsigned NOT NULL,
  `group_id` int(10) unsigned NOT NULL,
  `hepspec` float unsigned DEFAULT NULL,
  `memory` float unsigned DEFAULT NULL,
  `storage` float unsigned DEFAULT NULL,
  `bandwidth` float unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name_project_allocation` (`name`) USING BTREE,
  KEY `fk_project_project_allocation` (`project_id`),
  KEY `fk_group_project_allocation` (`group_id`),
  KEY `fk_allocation_project_allocation` (`top_level_allocation_id`),
  CONSTRAINT `fk_allocation_project_allocation` FOREIGN KEY (`top_level_allocation_id`) REFERENCES `top_level_allocation` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_group_project_allocation` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_project_project_allocation` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1741 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project_allocation`
--

LOCK TABLES `project_allocation` WRITE;
/*!40000 ALTER TABLE `project_allocation` DISABLE KEYS */;
/*!40000 ALTER TABLE `project_allocation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project_allocation_allowed_resource_type`
--

DROP TABLE IF EXISTS `project_allocation_allowed_resource_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_allocation_allowed_resource_type` (
  `project_allocation_id` int(10) unsigned NOT NULL,
  `resource_type_id` smallint(5) unsigned NOT NULL,
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`project_allocation_id`,`resource_type_id`),
  UNIQUE KEY `id` (`id`),
  KEY `fk_resource_project_allocation_allowed_resource_type` (`resource_type_id`),
  CONSTRAINT `fk_allocation_project_allocation_allowed_resource_type` FOREIGN KEY (`project_allocation_id`) REFERENCES `project_allocation` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_resource_project_allocation_allowed_resource_type` FOREIGN KEY (`resource_type_id`) REFERENCES `resource_type` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1589 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project_allocation_allowed_resource_type`
--

LOCK TABLES `project_allocation_allowed_resource_type` WRITE;
/*!40000 ALTER TABLE `project_allocation_allowed_resource_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `project_allocation_allowed_resource_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project_allocation_metadata`
--

DROP TABLE IF EXISTS `project_allocation_metadata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_allocation_metadata` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `project_id` int(11) unsigned NOT NULL,
  `attribute` varchar(50) NOT NULL,
  `value` varchar(100) DEFAULT NULL,
  `project_allocation_id` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=692 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project_allocation_metadata`
--

LOCK TABLES `project_allocation_metadata` WRITE;
/*!40000 ALTER TABLE `project_allocation_metadata` DISABLE KEYS */;
/*!40000 ALTER TABLE `project_allocation_metadata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project_metadata`
--

DROP TABLE IF EXISTS `project_metadata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_metadata` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `project_id` int(11) NOT NULL,
  `attribute` varchar(50) NOT NULL,
  `value` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `project_id_refs_id_7ebb86a2` (`project_id`)
) ENGINE=InnoDB AUTO_INCREMENT=394 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project_metadata`
--

LOCK TABLES `project_metadata` WRITE;
/*!40000 ALTER TABLE `project_metadata` DISABLE KEYS */;
/*!40000 ALTER TABLE `project_metadata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `region`
--

DROP TABLE IF EXISTS `region`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `region` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(100) DEFAULT NULL,
  `admin_group` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_region` (`name`) USING BTREE,
  KEY `fk_region` (`admin_group`),
  CONSTRAINT `fk_region` FOREIGN KEY (`admin_group`) REFERENCES `egroups` (`name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `region`
--

LOCK TABLES `region` WRITE;
/*!40000 ALTER TABLE `region` DISABLE KEYS */;
/*!40000 ALTER TABLE `region` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `resource_type`
--

DROP TABLE IF EXISTS `resource_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `resource_type` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `resource_class` varchar(24) NOT NULL,
  `hepspecs` float unsigned DEFAULT NULL,
  `memory` float unsigned DEFAULT NULL,
  `storage` float unsigned DEFAULT NULL,
  `bandwidth` float unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_resource_type` (`name`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `resource_type`
--

LOCK TABLES `resource_type` WRITE;
/*!40000 ALTER TABLE `resource_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `resource_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `top_level_allocation`
--

DROP TABLE IF EXISTS `top_level_allocation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `top_level_allocation` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `group_id` int(10) unsigned NOT NULL,
  `hepspec` float unsigned DEFAULT NULL,
  `memory` float unsigned DEFAULT NULL,
  `storage` float unsigned DEFAULT NULL,
  `bandwidth` float unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_top_level_allocation` (`name`) USING BTREE,
  KEY `fk_top_level_allocation` (`group_id`),
  CONSTRAINT `fk_top_level_allocation` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1880 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `top_level_allocation`
--

LOCK TABLES `top_level_allocation` WRITE;
/*!40000 ALTER TABLE `top_level_allocation` DISABLE KEYS */;
/*!40000 ALTER TABLE `top_level_allocation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `top_level_allocation_allowed_resource_type`
--

DROP TABLE IF EXISTS `top_level_allocation_allowed_resource_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `top_level_allocation_allowed_resource_type` (
  `top_level_allocation_id` int(10) unsigned NOT NULL,
  `resource_type_id` smallint(5) unsigned NOT NULL,
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `zone_id` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`top_level_allocation_id`,`zone_id`,`resource_type_id`),
  UNIQUE KEY `id` (`id`),
  KEY `fk_resource_top_level_allocation_allowed_resource_type` (`resource_type_id`),
  KEY `fk_zone_top_level_allocation_allowed_resource_type` (`zone_id`),
  CONSTRAINT `fk_allocation_top_level_allocation_allowed_resource_type` FOREIGN KEY (`top_level_allocation_id`) REFERENCES `top_level_allocation` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_resource_top_level_allocation_allowed_resource_type` FOREIGN KEY (`resource_type_id`) REFERENCES `resource_type` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_zone_top_level_allocation_allowed_resource_type` FOREIGN KEY (`zone_id`) REFERENCES `zone` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1598 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `top_level_allocation_allowed_resource_type`
--

LOCK TABLES `top_level_allocation_allowed_resource_type` WRITE;
/*!40000 ALTER TABLE `top_level_allocation_allowed_resource_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `top_level_allocation_allowed_resource_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `top_level_allocation_by_zone`
--

DROP TABLE IF EXISTS `top_level_allocation_by_zone`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `top_level_allocation_by_zone` (
  `top_level_allocation_id` int(10) unsigned NOT NULL,
  `zone_id` smallint(5) unsigned NOT NULL,
  `hepspec` float unsigned DEFAULT NULL,
  `memory` float unsigned DEFAULT NULL,
  `storage` float unsigned DEFAULT NULL,
  `bandwidth` float unsigned DEFAULT NULL,
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`top_level_allocation_id`,`zone_id`),
  UNIQUE KEY `id` (`id`),
  KEY `fk_zone_top_level_allocation_by_zone` (`zone_id`),
  CONSTRAINT `fk_allocation_top_level_allocation_by_zone` FOREIGN KEY (`top_level_allocation_id`) REFERENCES `top_level_allocation` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_zone_top_level_allocation_by_zone` FOREIGN KEY (`zone_id`) REFERENCES `zone` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1598 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `top_level_allocation_by_zone`
--

LOCK TABLES `top_level_allocation_by_zone` WRITE;
/*!40000 ALTER TABLE `top_level_allocation_by_zone` DISABLE KEYS */;
/*!40000 ALTER TABLE `top_level_allocation_by_zone` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_group_mapping`
--

DROP TABLE IF EXISTS `user_group_mapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_group_mapping` (
  `user_name` varchar(50) NOT NULL,
  `group_name` varchar(100) NOT NULL,
  PRIMARY KEY (`user_name`,`group_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_group_mapping`
--

LOCK TABLES `user_group_mapping` WRITE;
/*!40000 ALTER TABLE `user_group_mapping` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_group_mapping` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_roles`
--

DROP TABLE IF EXISTS `user_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_roles` (
  `user_name` varchar(50) NOT NULL,
  `sphere_type` varchar(20) NOT NULL,
  `sphere_name` varchar(50) NOT NULL,
  `role` varchar(50) NOT NULL,
  PRIMARY KEY (`user_name`,`sphere_type`,`sphere_name`,`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_roles`
--

LOCK TABLES `user_roles` WRITE;
/*!40000 ALTER TABLE `user_roles` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `zone`
--

DROP TABLE IF EXISTS `zone`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `zone` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(100) DEFAULT NULL,
  `region_id` smallint(5) unsigned DEFAULT NULL,
  `hepspecs` float unsigned DEFAULT NULL,
  `memory` float unsigned DEFAULT NULL,
  `storage` float unsigned DEFAULT NULL,
  `bandwidth` float unsigned DEFAULT NULL,
  `hepspec_overcommit` float unsigned DEFAULT '1',
  `memory_overcommit` float unsigned DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_zone` (`region_id`,`name`) USING BTREE,
  CONSTRAINT `fk_zone` FOREIGN KEY (`region_id`) REFERENCES `region` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `zone`
--

LOCK TABLES `zone` WRITE;
/*!40000 ALTER TABLE `zone` DISABLE KEYS */;
/*!40000 ALTER TABLE `zone` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `zone_allowed_resource_type`
--

DROP TABLE IF EXISTS `zone_allowed_resource_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `zone_allowed_resource_type` (
  `zone_id` smallint(5) unsigned NOT NULL,
  `resource_type_id` smallint(5) unsigned NOT NULL,
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`zone_id`,`resource_type_id`),
  UNIQUE KEY `id` (`id`),
  KEY `fk_resource_zone_allowed_resource_type` (`resource_type_id`),
  CONSTRAINT `fk_resource_zone_allowed_resource_type` FOREIGN KEY (`resource_type_id`) REFERENCES `resource_type` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_zone_zone_allowed_resource_type` FOREIGN KEY (`zone_id`) REFERENCES `zone` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `zone_allowed_resource_type`
--

LOCK TABLES `zone_allowed_resource_type` WRITE;
/*!40000 ALTER TABLE `zone_allowed_resource_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `zone_allowed_resource_type` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2012-06-08 14:27:21
