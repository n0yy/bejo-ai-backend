import os
from langchain_community.utilities import SQLDatabase


def get_database():
    """
    Return a SQLDatabase object based on environment variables.

    The following environment variables are used, with default values if not present:
    - DB_USER: the username for the database, default "test"
    - DB_PASSWORD: the password for the database, default "Test_1234"
    - DB_HOST: the hostname of the database, default "localhost"
    - DB_PORT: the port number of the database, default "3306"
    - DB_NAME: the name of the database, default "expb7"

    The connection string is constructed in the form
    "mysql+pymysql://<user>:<password>@<host>:<port>/<db_name>".
    """
    db_user = os.getenv("DB_USER", "test")
    db_password = os.getenv("DB_PASSWORD", "Test_1234")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "expb7")

    connection_string = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )

    return SQLDatabase.from_uri(connection_string)
