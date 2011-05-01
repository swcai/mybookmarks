DROP TABLE IF EXISTS bookmarks;
CREATE TABLE bookmarks (
    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    title text NOT NULL,
    url text NOT NULL,
    last_modified long NOT NULL
);
