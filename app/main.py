"""Small bike-share API backed by PostGIS. It exists to give the test suite something real to verify."""

import os
from collections.abc import Iterator
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Response
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db:5432/bikeshare")

app = FastAPI(title="Bike-share stations API")

Latitude = Annotated[float, Query(ge=-90, le=90)]
Longitude = Annotated[float, Query(ge=-180, le=180)]

STATION_COLUMNS = "s.id, s.name, s.capacity, ST_Y(s.geom) AS lat, ST_X(s.geom) AS lon"
POINT = "ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)"


class NewStation(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    capacity: int = Field(gt=0)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


def get_db() -> Iterator[psycopg.Connection]:
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as connection:
        yield connection


Db = Annotated[psycopg.Connection, Depends(get_db)]


@app.get("/health")
def health(db: Db) -> dict:
    db.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/areas")
def list_areas(db: Db) -> list[dict]:
    return db.execute(
        """
        SELECT a.id,
               a.name,
               count(s.id) AS station_count,
               round((ST_Area(a.geom::geography) / 1e6)::numeric, 3)::float AS area_km2
        FROM service_areas a
        LEFT JOIN stations s ON ST_Covers(a.geom, s.geom)
        GROUP BY a.id
        ORDER BY a.id
        """
    ).fetchall()


@app.get("/areas/{area_id}/stations")
def stations_in_area(area_id: int, db: Db) -> list[dict]:
    if db.execute("SELECT 1 FROM service_areas WHERE id = %s", (area_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Service area not found")
    return db.execute(
        f"""
        SELECT {STATION_COLUMNS}
        FROM stations s
        JOIN service_areas a ON ST_Covers(a.geom, s.geom)
        WHERE a.id = %s
        ORDER BY s.id
        """,
        (area_id,),
    ).fetchall()


@app.get("/stations/nearest")
def nearest_stations(
    lat: Latitude,
    lon: Longitude,
    db: Db,
    limit: Annotated[int, Query(ge=1, le=50)] = 3,
) -> list[dict]:
    return db.execute(
        f"""
        SELECT {STATION_COLUMNS},
               round(ST_Distance(s.geom::geography, {POINT}::geography)::numeric, 1)::float AS distance_m
        FROM stations s
        ORDER BY s.geom::geography <-> {POINT}::geography, s.id
        LIMIT %(limit)s
        """,
        {"lat": lat, "lon": lon, "limit": limit},
    ).fetchall()


@app.get("/stations/within")
def stations_within(
    lat: Latitude,
    lon: Longitude,
    radius_m: Annotated[float, Query(ge=0, le=50_000)],
    db: Db,
) -> list[dict]:
    return db.execute(
        f"""
        SELECT {STATION_COLUMNS}
        FROM stations s
        WHERE ST_DWithin(s.geom::geography, {POINT}::geography, %(radius_m)s)
        ORDER BY s.id
        """,
        {"lat": lat, "lon": lon, "radius_m": radius_m},
    ).fetchall()


@app.post("/stations", status_code=201)
def create_station(station: NewStation, db: Db) -> dict:
    try:
        created = db.execute(
            f"""
            INSERT INTO stations (name, capacity, geom)
            VALUES (%(name)s, %(capacity)s, {POINT})
            RETURNING id, name, capacity, ST_Y(geom) AS lat, ST_X(geom) AS lon
            """,
            station.model_dump(),
        ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="A station with this name already exists")

    area = db.execute(
        f"SELECT name FROM service_areas WHERE ST_Covers(geom, {POINT})",
        {"lat": station.lat, "lon": station.lon},
    ).fetchone()
    return {**created, "area": area["name"] if area else None}


@app.delete("/stations/{station_id}", status_code=204)
def delete_station(station_id: int, db: Db) -> Response:
    deleted = db.execute("DELETE FROM stations WHERE id = %s RETURNING id", (station_id,)).fetchone()
    if deleted is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return Response(status_code=204)
