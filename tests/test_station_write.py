import pytest

INSIDE_ZONA_4 = {"lat": 14.6200, "lon": -90.5150}
OUTSIDE_ALL_AREAS = {"lat": 14.7000, "lon": -90.4000}


def test_created_station_is_stored_with_the_right_geometry(api, db, unique_name, created_station_ids):
    response = api.post("/stations", json={"name": unique_name, "capacity": 14, **INSIDE_ZONA_4})

    assert response.status_code == 201
    body = response.json()
    created_station_ids.append(body["id"])

    row = db.execute(
        "SELECT name, capacity, ST_X(geom) AS lon, ST_Y(geom) AS lat, ST_SRID(geom) AS srid FROM stations WHERE id = %s",
        (body["id"],),
    ).fetchone()
    assert row == {"name": unique_name, "capacity": 14, "lon": INSIDE_ZONA_4["lon"], "lat": INSIDE_ZONA_4["lat"], "srid": 4326}


def test_response_names_the_area_that_covers_the_station(api, unique_name, created_station_ids):
    body = api.post("/stations", json={"name": unique_name, "capacity": 5, **INSIDE_ZONA_4}).json()
    created_station_ids.append(body["id"])

    assert body["area"] == "Zona 4"


def test_station_outside_every_area_has_no_area(api, unique_name, created_station_ids):
    body = api.post("/stations", json={"name": unique_name, "capacity": 5, **OUTSIDE_ALL_AREAS}).json()
    created_station_ids.append(body["id"])

    assert body["area"] is None


def test_new_station_shows_up_in_area_and_nearest_queries(api, db, unique_name, created_station_ids):
    body = api.post("/stations", json={"name": unique_name, "capacity": 5, **INSIDE_ZONA_4}).json()
    created_station_ids.append(body["id"])
    zona_4 = db.execute("SELECT id FROM service_areas WHERE name = 'Zona 4'").fetchone()["id"]

    in_area = [s["id"] for s in api.get(f"/areas/{zona_4}/stations").json()]
    nearest = api.get("/stations/nearest", params={**INSIDE_ZONA_4, "limit": 1}).json()

    assert body["id"] in in_area
    assert nearest[0]["id"] == body["id"]
    assert nearest[0]["distance_m"] == 0


def test_duplicate_name_is_rejected_and_nothing_is_written(api, db):
    before = db.execute("SELECT count(*) AS n FROM stations").fetchone()["n"]

    response = api.post("/stations", json={"name": "Parque Central", "capacity": 5, **INSIDE_ZONA_4})

    assert response.status_code == 409
    assert db.execute("SELECT count(*) AS n FROM stations").fetchone()["n"] == before


@pytest.mark.parametrize(
    "override",
    [
        {"lat": 91},
        {"lon": -181},
        {"capacity": 0},
        {"capacity": -3},
        {"capacity": "many"},
        {"name": ""},
        {"name": "x" * 81},
    ],
    ids=["lat-out-of-range", "lon-out-of-range", "capacity-zero", "capacity-negative", "capacity-not-a-number", "name-empty", "name-too-long"],
)
def test_invalid_station_is_rejected_and_nothing_is_written(api, db, unique_name, override):
    before = db.execute("SELECT count(*) AS n FROM stations").fetchone()["n"]
    payload = {"name": unique_name, "capacity": 5, **INSIDE_ZONA_4, **override}

    response = api.post("/stations", json=payload)

    assert response.status_code == 422
    assert db.execute("SELECT count(*) AS n FROM stations").fetchone()["n"] == before


def test_delete_removes_the_row(api, db, unique_name):
    station_id = api.post("/stations", json={"name": unique_name, "capacity": 5, **INSIDE_ZONA_4}).json()["id"]

    response = api.delete(f"/stations/{station_id}")

    assert response.status_code == 204
    assert db.execute("SELECT 1 FROM stations WHERE id = %s", (station_id,)).fetchone() is None


def test_delete_unknown_station_returns_404(api):
    assert api.delete("/stations/999999").status_code == 404
