
DROP TABLE IF EXISTS users;
CREATE TABLE `users` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES users WRITE;
INSERT INTO users VALUES(7,'山田太郎','taro@example.com');
INSERT INTO users VALUES(8,'Suzuki','suzuki@example.com');
INSERT INTO users VALUES(9,'','empty@example.com');
INSERT INTO users VALUES(10,'カンマ,入り','comma@example.com');
INSERT INTO users VALUES(11,'ダブル"クォート','quote@example.com');
INSERT INTO users VALUES(12,'改行\nテスト','newline@example.com');
INSERT INTO users VALUES(13,'テストユーザー','test@example.com');
INSERT INTO users VALUES(14,'NULLMAN','NULL');
UNLOCK TABLES;
