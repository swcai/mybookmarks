DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    email text NOT NULL,
    username text NOT NULL,
    password text NOT NULL,
    alias text NOT NULL
);

DROP TABLE IF EXISTS bookmarks;
CREATE TABLE bookmarks (
    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    title text NOT NULL,
    url text NOT NULL,
    user_id integer NOT NULL,
    tag integer DEFAULT 0,
    modified_at long NOT NULL
);
