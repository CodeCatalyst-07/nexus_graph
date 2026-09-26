from neo4j import GraphDatabase, Driver
from typing import Optional, Dict, Any, List
import logging
from app.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE

logger = logging.getLogger("nexusgraph.database")
_driver: Optional[Driver] = None

def get_driver() -> Driver:
    global _driver
    if _driver is None:
        logger.info(f"Connecting to Neo4j at {NEO4J_URI}")
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
            max_connection_lifetime=30 * 60,
            max_connection_pool_size=50,
            connection_acquisition_timeout=10.0
        )
        _driver.verify_connectivity()
        logger.info("Neo4j driver connectivity verified.")
    return _driver

def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None
        logger.info("Neo4j driver connection closed.")

def run_query(query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    driver = get_driver()
    params = parameters or {}
    with driver.session(database=NEO4J_DATABASE) as session:
        result = session.run(query, params)
        return [record.data() for record in result]

def init_constraints():
    constraints = [
        "CREATE CONSTRAINT customer_email_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.email IS UNIQUE;",
        "CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;",
        "CREATE CONSTRAINT ticket_id_unique IF NOT EXISTS FOR (t:SupportTicket) REQUIRE t.id IS UNIQUE;",
        "CREATE CONSTRAINT issue_id_unique IF NOT EXISTS FOR (i:Issue) REQUIRE i.id IS UNIQUE;",
        "CREATE CONSTRAINT resolution_id_unique IF NOT EXISTS FOR (r:Resolution) REQUIRE r.id IS UNIQUE;",
        "CREATE CONSTRAINT outcome_id_unique IF NOT EXISTS FOR (o:Outcome) REQUIRE o.id IS UNIQUE;",
        "CREATE CONSTRAINT interaction_id_unique IF NOT EXISTS FOR (n:Interaction) REQUIRE n.id IS UNIQUE;"
    ]
    driver = get_driver()
    with driver.session(database=NEO4J_DATABASE) as session:
        for c in constraints:
            session.run(c)
    logger.info("Neo4j constraints verified and active.")
