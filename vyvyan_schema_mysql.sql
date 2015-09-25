-- MySQL dump 10.13  Distrib 5.1.54, for debian-linux-gnu (i686)
--

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
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups` (
  `description` varchar(150) DEFAULT NULL,
  `sudo_cmds` varchar(2000) DEFAULT NULL,
  `groupname` varchar(64) NOT NULL,
  `site_id` varchar(3) NOT NULL,
  `realm` varchar(10) NOT NULL,
  `gid` int(11) NOT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`groupname`,`realm`,`site_id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kv`
--

DROP TABLE IF EXISTS `kv`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kv` (
  `key` varchar(100) DEFAULT NULL,
  `value` varchar(200) DEFAULT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_group_mapping`
--

DROP TABLE IF EXISTS `user_group_mapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_group_mapping` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `groups_id` bigint(20) unsigned DEFAULT NULL,
  `users_id` bigint(20) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `user_group_mapping_groups_id_fkey` (`groups_id`),
  KEY `user_group_mapping_users_id_fkey` (`users_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `ssh_public_key` varchar(1500) DEFAULT NULL,
  `username` varchar(64) NOT NULL,
  `site_id` varchar(3) NOT NULL,
  `realm` varchar(10) NOT NULL,
  `uid` int(11) NOT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `type` varchar(15) DEFAULT NULL,
  `hdir` varchar(100) DEFAULT NULL,
  `shell` varchar(100) DEFAULT NULL,
  `active` tinyint(1) DEFAULT '1',
  `email` varchar(100) DEFAULT NULL,
  UNIQUE KEY `id` (`id`),
  PRIMARY KEY (`username`,`realm`,`site_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
