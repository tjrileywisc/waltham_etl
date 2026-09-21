from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import json


def get_db() -> Engine:

    config = json.load(open("config.json"))

    username = config["postgres"]["accounts"]["writable"]["username"]
    password = config["postgres"]["accounts"]["writable"]["password"]
    host = config["postgres"]["host"]
    db = config["postgres"]["database"]

    url = f"postgresql+psycopg://{username}:{password}@{host}/{db}"

    con = create_engine(url)

    return con
