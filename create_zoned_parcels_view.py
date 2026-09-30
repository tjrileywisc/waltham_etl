
from sqlalchemy import text

from connect_db import get_db

con = get_db()

# One row per parcel, tagged with whichever zoning district covers the most of its
# area. A parcel that straddles a zoning boundary technically intersects more than
# one district (ST_Intersects), but is only meant to have one zone -- so pick the
# majority district by overlap area (DISTINCT ON ... ORDER BY overlap area desc)
# instead of emitting one row per intersected zone.
CREATE_VIEW_SQL = """
CREATE OR REPLACE VIEW public.vw_waltham_zoned_parcels_2026 AS
SELECT DISTINCT ON (p."LOC_ID")
    p."LOC_ID",
    p."MAP_PAR_ID",
    z."NAME" AS zone,
    ST_Transform(p.geom, 4326) AS geom
FROM
    public."M308TaxPar_CY26_FY26" AS p
JOIN
    public.waltham_zoning z ON ST_Intersects(z.geom, p.geom)
ORDER BY
    p."LOC_ID", ST_Area(ST_Intersection(z.geom, p.geom)) DESC;
"""

with con.begin() as conn:
    conn.execute(text(CREATE_VIEW_SQL))

print("Created view 'vw_waltham_zoned_parcels_2026'")
