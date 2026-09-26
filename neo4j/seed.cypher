// Idempotent Seed Query for Demo Customer and Product
MERGE (c:Customer {email: 'alice@techcorp.io'})
ON CREATE SET c.name = 'Alice Chen', c.company = 'TechCorp Global'

MERGE (p:Product {id: 'PROD-GDS-01'})
ON CREATE SET p.name = 'Graph Data Science Workspace', p.category = 'Cloud Graph Compute'

MERGE (c)-[:PURCHASED {purchasedAt: '2026-09-01'}]->(p)

RETURN c.email AS customerEmail, c.name AS customerName, p.id AS productId, p.name AS productName;
