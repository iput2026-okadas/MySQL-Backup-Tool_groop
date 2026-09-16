
DROP TABLE IF EXISTS users_sample;
CREATE TABLE `users_sample` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sample_data` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES users_sample WRITE;
UNLOCK TABLES;
