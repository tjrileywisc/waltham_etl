
from pathlib import Path

from sqlalchemy import text

from connect_db import get_db

VIEWS_DIR = Path(__file__).parent / "views"

con = get_db()

for path in sorted(VIEWS_DIR.glob("*.sql")):
    with con.begin() as conn:
        conn.execute(text(path.read_text()))
    print(f"Applied {path.name}")
