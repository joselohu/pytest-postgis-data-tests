-- Fictional bike-share network laid over Guatemala City. Coordinates are approximate.

INSERT INTO service_areas (name, geom) VALUES
    ('Centro Historico', ST_MakeEnvelope(-90.520, 14.632, -90.505, 14.650, 4326)),
    ('Zona 4',           ST_MakeEnvelope(-90.522, 14.612, -90.510, 14.628, 4326)),
    ('Zona 10',          ST_MakeEnvelope(-90.522, 14.590, -90.500, 14.608, 4326));

INSERT INTO stations (name, capacity, geom) VALUES
    ('Parque Central',       20, ST_SetSRID(ST_MakePoint(-90.5133, 14.6418), 4326)),
    ('Mercado Central',      12, ST_SetSRID(ST_MakePoint(-90.5118, 14.6427), 4326)),
    ('Teatro Nacional',      15, ST_SetSRID(ST_MakePoint(-90.5180, 14.6335), 4326)),
    ('Cuatro Grados Norte',  18, ST_SetSRID(ST_MakePoint(-90.5165, 14.6205), 4326)),
    ('Terminal Zona 4',      10, ST_SetSRID(ST_MakePoint(-90.5200, 14.6150), 4326)),
    ('Obelisco',             25, ST_SetSRID(ST_MakePoint(-90.5170, 14.5975), 4326)),
    ('Zona Viva',            30, ST_SetSRID(ST_MakePoint(-90.5120, 14.6010), 4326)),
    ('Plaza Fontabella',     16, ST_SetSRID(ST_MakePoint(-90.5085, 14.5995), 4326)),
    -- Sits exactly on the east edge of Zona 10: the boundary case.
    ('Borde Zona 10',         8, ST_SetSRID(ST_MakePoint(-90.5000, 14.6000), 4326)),
    -- Outside every service area.
    ('Aeropuerto La Aurora', 22, ST_SetSRID(ST_MakePoint(-90.5275, 14.5833), 4326));
