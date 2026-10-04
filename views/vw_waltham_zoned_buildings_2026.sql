-- One row per building, tagged with whichever zoning district covers the most of its
-- footprint area. A building straddling a zoning boundary technically intersects more
-- than one district (ST_Intersects), but is only meant to have one zone -- so pick the
-- majority district by overlap area (DISTINCT ON ... ORDER BY overlap area desc)
-- instead of emitting one row per intersected zone.
CREATE OR REPLACE VIEW public.vw_waltham_zoned_buildings_2026 AS
SELECT DISTINCT ON (b."STRUCT_ID")
    b."STRUCT_ID",
    z."NAME",
    ST_Transform(b.geometry, 4326) AS geom
FROM
    public.waltham_buildings AS b
JOIN
    public.waltham_zoning z ON ST_Intersects(z.geom, b.geometry)
ORDER BY
    b."STRUCT_ID", ST_Area(ST_Intersection(z.geom, b.geometry)) DESC;
