"""Checks on the stored data itself, independent of the API."""

import pytest

pytestmark = pytest.mark.data_quality

# Rough bounding box of the Guatemala City metropolitan area.
CITY_BBOX = "ST_MakeEnvelope(-90.70, 14.45, -90.35, 14.75, 4326)"


@pytest.mark.parametrize("table", ["stations", "service_areas"])
def test_geometries_are_valid_and_use_wgs84(db, table):
    bad = db.execute(f"SELECT id FROM {table} WHERE NOT ST_IsValid(geom) OR ST_SRID(geom) <> 4326").fetchall()

    assert bad == []


def test_service_areas_do_not_overlap(db):
    overlapping = db.execute(
        """
        SELECT a.name AS first, b.name AS second
        FROM service_areas a
        JOIN service_areas b ON a.id < b.id AND ST_Intersects(a.geom, b.geom)
        """
    ).fetchall()

    assert overlapping == []


def test_no_station_belongs_to_two_areas(db):
    shared = db.execute(
        """
        SELECT s.name
        FROM stations s
        JOIN service_areas a ON ST_Covers(a.geom, s.geom)
        GROUP BY s.id
        HAVING count(*) > 1
        """
    ).fetchall()

    assert shared == []


def test_every_station_is_inside_the_city(db):
    outside = db.execute(f"SELECT name FROM stations WHERE NOT ST_Covers({CITY_BBOX}, geom)").fetchall()

    assert outside == []


def test_no_two_stations_share_a_location(db):
    duplicates = db.execute(
        """
        SELECT a.name AS first, b.name AS second
        FROM stations a
        JOIN stations b ON a.id < b.id AND ST_DWithin(a.geom::geography, b.geom::geography, 5)
        """
    ).fetchall()

    assert duplicates == []


def test_spatial_indexes_exist(db):
    indexed = {
        row["tablename"]
        for row in db.execute("SELECT tablename FROM pg_indexes WHERE indexdef ILIKE '%USING gist%'")
    }

    assert {"stations", "service_areas"} <= indexed
