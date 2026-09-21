"""
Create users in the database
"""

import psycopg
from psycopg import sql

from config import get_config


def main() -> None:
    config = get_config()
    pg = config["postgres"]
    database = pg["database"]
    admin = pg["accounts"]["writable"]

    host, _, port = pg["host"].partition(":")

    conn = psycopg.connect(
        host=host,
        port=int(port) if port else 5432,
        dbname=database,
        user=admin["username"],
        password=admin["password"],
        autocommit=True,
    )

    with conn.cursor() as cur:
        for name, account in pg["accounts"].items():
            username = account["username"]
            password = account["password"]

            if username == admin["username"]:
                # bootstrapped by the postgres image itself via POSTGRES_PASSWORD
                continue

            cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (username,))
            if cur.fetchone():
                cur.execute(
                    sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
                        sql.Identifier(username), sql.Literal(password)
                    )
                )
                print(f"Updated password for role {username!r}")
            else:
                cur.execute(
                    sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {}").format(
                        sql.Identifier(username), sql.Literal(password)
                    )
                )
                print(f"Created role {username!r}")

            cur.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(database), sql.Identifier(username)
                )
            )
            cur.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(username)))

            if name == "readonly":
                cur.execute(
                    sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA public TO {}").format(sql.Identifier(username))
                )
                cur.execute(
                    sql.SQL(
                        "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA public GRANT SELECT ON TABLES TO {}"
                    ).format(sql.Identifier(admin["username"]), sql.Identifier(username))
                )
                print(f"Granted read-only privileges to {username!r}")

    conn.close()


if __name__ == "__main__":
    main()
