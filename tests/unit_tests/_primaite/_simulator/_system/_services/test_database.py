import json

import pytest

from primaite.simulator.network.hardware.base import Node
from primaite.simulator.system.services.database import DatabaseService

DDL = """
CREATE TABLE IF NOT EXISTS user (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(50) NOT NULL,
email VARCHAR(50) NOT NULL,
age INT,
city VARCHAR(50),
occupation VARCHAR(50)
);"""

USER_INSERT_STATEMENTS = [
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('John Doe', 'johndoe@example.com', 32, 'New York', 'Engineer');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('Jane Smith', 'janesmith@example.com', 27, 'Los Angeles', 'Designer');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('Bob Johnson', 'bobjohnson@example.com', 45, 'Chicago', 'Manager');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('Alice Lee', 'alicelee@example.com', 22, 'San Francisco', 'Student');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('David Kim', 'davidkim@example.com', 38, 'Houston', 'Consultant');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('Emily Chen', 'emilychen@example.com', 29, 'Seattle', 'Software Developer');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('Frank Wang', 'frankwang@example.com', 55, 'New York', 'Entrepreneur');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('Grace Park', 'gracepark@example.com', 31, 'Los Angeles', 'Marketing Specialist');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('Henry Wu', 'henrywu@example.com', 40, 'Chicago', 'Accountant');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('Isabella Kim', 'isabellakim@example.com', 26, 'San Francisco', 'Graphic Designer');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('Jake Lee', 'jakelee@example.com', 33, 'Houston', 'Sales Manager');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('Kelly Chen', 'kellychen@example.com', 28, 'Seattle', 'Web Developer');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('Lucas Liu', 'lucasliu@example.com', 42, 'New York', 'Lawyer');",
    "INSERT INTO user (name, email, age, city, occupation) VALUES ('Maggie Wang', 'maggiewang@example.com', 30, 'Los Angeles', 'Data Analyst');",
]


@pytest.fixture(scope="function")
def database_server() -> Node:
    node = Node(hostname="db_node")
    node.software_manager.add_service(DatabaseService)
    node.software_manager.services["Database"].start()
    return node


@pytest.fixture(scope="function")
def database(database_server) -> DatabaseService:
    database: DatabaseService = database_server.software_manager.services["Database"]  # noqa
    database.receive(DDL, None)
    for script in USER_INSERT_STATEMENTS:
        database.receive(script, None)
    return database


def test_creation(database_server):
    database_server.software_manager.show()


def test_db_population(database):
    database.show()
    assert database.tables() == ["user"]
