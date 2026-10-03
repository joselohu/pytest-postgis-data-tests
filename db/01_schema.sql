CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE service_areas (
    id   serial PRIMARY KEY,
    name text NOT NULL UNIQUE,
    geom geometry(Polygon, 4326) NOT NULL
);

CREATE TABLE stations (
    id       serial PRIMARY KEY,
    name     text NOT NULL UNIQUE,
    capacity integer NOT NULL CHECK (capacity > 0),
    geom     geometry(Point, 4326) NOT NULL
);

CREATE INDEX service_areas_geom_idx ON service_areas USING gist (geom);
CREATE INDEX stations_geom_idx ON stations USING gist (geom);
