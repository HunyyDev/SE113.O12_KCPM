import os
from neo4j import GraphDatabase
from .. import logger

logger.info("Connecting to neo4j")

URI = os.environ.get("NEO4J_URI")
AUTH = (os.environ.get("NEO4J_USERNAME"), os.environ.get("NEO4J_PASSWORD"))

driver = GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()
driver.execute_query(
    "CREATE CONSTRAINT uid IF NOT EXISTS FOR (p:Person) REQUIRE p.uid IS UNIQUE"
)
