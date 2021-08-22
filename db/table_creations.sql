-- TABLES

CREATE TABLE IF NOT EXISTS rating (
	author text,
	element_id text,
	comment text,
	type text,
	rate real
);

CREATE TABLE IF NOT EXISTS event (
	author text,
	date text,
	comment text
);

CREATE TABLE IF NOT EXISTS character (
	name text,
	description text,
	category text,
	image_link text,
	page_id text,
	rarity INTEGER
);

CREATE TABLE IF NOT EXISTS background (
    name text,
    type text -- movie, shorts, rides, ...
);

CREATE TABLE IF NOT EXISTS affiliation (
    name text UNIQUE
);

-- JOINTURE TABLES

CREATE TABLE IF NOT EXISTS appearance (
    character_id INTEGER,
    background_id INTEGER,
    PRIMARY KEY(character_id, background_id),
    FOREIGN KEY(character_id)
        REFERENCES character (rowid)
            ON DELETE CASCADE
            ON UPDATE NO ACTION,
    FOREIGN KEY(background_id)
        REFERENCES background (rowid)
            ON DELETE CASCADE
            ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS character_affiliation (
    character_id INTEGER,
    affiliation_id INTEGER,
    PRIMARY KEY(character_id, affiliation_id),
    FOREIGN KEY(character_id)
        REFERENCES character (rowid)
            ON DELETE CASCADE
            ON UPDATE NO ACTION,
    FOREIGN KEY(affiliation_id)
        REFERENCES affiliation (rowid)
            ON DELETE CASCADE
            ON UPDATE NO ACTION
);