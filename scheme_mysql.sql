set SESSION storage_engine = "InnoDB";
set SESSION time_zone = "+0:00";
alter DATABASE CHARACTER set "utf8";

DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(100) NOT NULL,
    alias VARCHAR(100) NOT NULL
);

DROP TABLE IF EXISTS bookmarks;
CREATE TABLE bookmarks (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(512) NOT NULL,
    url VARCHAR(512) NOT NULL,
    user_id INT NOT NULL,
    tag INT DEFAULT 0,
    modified_at INT NOT NULL
);
