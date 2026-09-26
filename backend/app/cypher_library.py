# Pre-compiled, Parameterized Cypher Library for NexusGraph Support
# ZERO string concatenation. Strictly parameter-bound queries ($parameters).

SEED_CUSTOMER_PRODUCT = """
MERGE (c:Customer {email: $email})
ON CREATE SET c.name = $name, c.company = $company
MERGE (p:Product {id: $productId})
ON CREATE SET p.name = $productName, p.category = $category
MERGE (c)-[:PURCHASED {purchasedAt: '2026-09-01'}]->(p)
RETURN c.email AS customerEmail, c.name AS customerName, p.id AS productId, p.name AS productName;
"""

CHECK_CUSTOMER_EXISTS = """
MATCH (c:Customer {email: $email})
RETURN c.email AS email, c.name AS name, c.company AS company
LIMIT 1;
"""

CREATE_INITIAL_TICKET = """
MATCH (c:Customer {email: $email})
MATCH (p:Product {id: $productId})
CREATE (t:SupportTicket {
    id: $ticketId,
    status: 'OPEN',
    priority: 'HIGH',
    createdAt: datetime(),
    updatedAt: datetime()
})
CREATE (i:Issue {
    id: $issueId,
    errorCode: $errorCode,
    description: $description
})
CREATE (r:Resolution {
    id: $resolutionId,
    actionName: $actionName,
    instructions: $instructions,
    tier: 1
})
CREATE (o:Outcome {
    id: $outcomeId,
    status: 'PENDING',
    feedback: 'Awaiting customer verification',
    recordedAt: datetime()
})
CREATE (int:Interaction {
    id: $interactionId,
    userQuery: $userQuery,
    agentReply: $agentReply,
    timestamp: datetime()
})
CREATE (c)-[:OPENED_TICKET]->(t)
CREATE (t)-[:TARGETS]->(p)
CREATE (t)-[:EXHIBITS]->(i)
CREATE (t)-[:ATTEMPTED]->(r)
CREATE (r)-[:HAS_OUTCOME]->(o)
CREATE (t)-[:HAS_INTERACTION]->(int)
RETURN t.id AS ticketId, t.status AS ticketStatus, r.actionName AS prescribedAction;
"""

GET_ACTIVE_TICKETS = """
MATCH (c:Customer {email: $email})-[:OPENED_TICKET]->(t:SupportTicket)
WHERE t.status IN ['OPEN', 'ESCALATED']
MATCH (t)-[:TARGETS]->(p:Product)
MATCH (t)-[:EXHIBITS]->(i:Issue)
OPTIONAL MATCH (t)-[:ATTEMPTED]->(r:Resolution)-[:HAS_OUTCOME]->(o:Outcome)
WITH t, p, i, r, o
ORDER BY o.recordedAt DESC
WITH t, p, i, collect({resolution: r, outcome: o})[0] AS latestPair
RETURN t.id AS ticketId,
       t.status AS ticketStatus,
       p.id AS productId,
       p.name AS productName,
       i.errorCode AS errorCode,
       i.description AS issueDescription,
       latestPair.resolution.id AS resolutionId,
       latestPair.resolution.actionName AS lastActionName,
       latestPair.resolution.instructions AS lastInstructions,
       latestPair.outcome.id AS outcomeId,
       latestPair.outcome.status AS lastOutcomeStatus,
       t.updatedAt AS ticketUpdatedAt
ORDER BY t.updatedAt DESC;
"""

MUTATE_TICKET_ESCALATE = """
MATCH (t:SupportTicket {id: $ticketId})
MATCH (o:Outcome {id: $outcomeId})
SET o.status = 'FAILED',
    o.feedback = $feedback,
    o.recordedAt = datetime(),
    t.status = 'ESCALATED',
    t.updatedAt = datetime()
CREATE (r2:Resolution {
    id: $newResolutionId,
    actionName: $newActionName,
    instructions: $newInstructions,
    tier: 2
})
CREATE (o2:Outcome {
    id: $newOutcomeId,
    status: 'PENDING',
    feedback: 'Ticket queued for Tier-2 engineering review',
    recordedAt: datetime()
})
CREATE (int:Interaction {
    id: $interactionId,
    userQuery: $userQuery,
    agentReply: $agentReply,
    timestamp: datetime()
})
CREATE (t)-[:ATTEMPTED]->(r2)
CREATE (r2)-[:HAS_OUTCOME]->(o2)
CREATE (t)-[:HAS_INTERACTION]->(int)
RETURN t.status AS updatedTicketStatus, r2.actionName AS nextActionName;
"""

MUTATE_TICKET_RESOLVE = """
MATCH (t:SupportTicket {id: $ticketId})
MATCH (o:Outcome {id: $outcomeId})
SET o.status = 'SUCCESS',
    o.feedback = $feedback,
    o.recordedAt = datetime(),
    t.status = 'RESOLVED',
    t.updatedAt = datetime()
CREATE (int:Interaction {
    id: $interactionId,
    userQuery: $userQuery,
    agentReply: $agentReply,
    timestamp: datetime()
})
CREATE (t)-[:HAS_INTERACTION]->(int)
RETURN t.status AS updatedTicketStatus;
"""

GET_CUSTOMER_SUBGRAPH = """
MATCH (c:Customer {email: $email})
OPTIONAL MATCH (c)-[r1:PURCHASED]->(p:Product)
OPTIONAL MATCH (c)-[r2:OPENED_TICKET]->(t:SupportTicket)
OPTIONAL MATCH (t)-[r3:TARGETS]->(tp:Product)
OPTIONAL MATCH (t)-[r4:EXHIBITS]->(i:Issue)
OPTIONAL MATCH (t)-[r5:ATTEMPTED]->(res:Resolution)
OPTIONAL MATCH (res)-[r6:HAS_OUTCOME]->(out:Outcome)
RETURN c, p, t, tp, i, res, out, r1, r2, r3, r4, r5, r6;
"""

RESET_DEMO_STATE = """
MATCH (c:Customer {email: $email})
OPTIONAL MATCH (c)-[:OPENED_TICKET]->(t:SupportTicket)
OPTIONAL MATCH (t)-[:EXHIBITS]->(i:Issue)
OPTIONAL MATCH (t)-[:ATTEMPTED]->(r:Resolution)
OPTIONAL MATCH (r)-[:HAS_OUTCOME]->(o:Outcome)
OPTIONAL MATCH (t)-[:HAS_INTERACTION]->(int:Interaction)
DETACH DELETE t, i, r, o, int;
"""

GET_ACTIVE_TICKET_FOR_PRODUCT = """
MATCH (c:Customer {email: $email})-[:OPENED_TICKET]->(t:SupportTicket)-[:TARGETS]->(p:Product {id: $productId})
WHERE t.status IN ['OPEN', 'ESCALATED']
MATCH (t)-[:EXHIBITS]->(i:Issue)
OPTIONAL MATCH (t)-[:ATTEMPTED]->(r:Resolution)-[:HAS_OUTCOME]->(o:Outcome)
WITH t, p, i, r, o
ORDER BY o.recordedAt DESC
WITH t, p, i, collect({resolution: r, outcome: o})[0] AS latestPair
RETURN t.id AS ticketId,
       t.status AS ticketStatus,
       p.id AS productId,
       p.name AS productName,
       i.errorCode AS errorCode,
       i.description AS issueDescription,
       latestPair.resolution.id AS resolutionId,
       latestPair.resolution.actionName AS lastActionName,
       latestPair.resolution.instructions AS lastInstructions,
       latestPair.outcome.id AS outcomeId,
       latestPair.outcome.status AS lastOutcomeStatus,
       t.updatedAt AS ticketUpdatedAt
LIMIT 1;
"""

GET_TICKET_COUNT_FOR_CUSTOMER = """
MATCH (c:Customer {email: $email})-[:OPENED_TICKET]->(t:SupportTicket)
RETURN count(t) AS ticketCount;
"""

ENSURE_PRODUCT_CATALOG_NODE = """
MERGE (p:Product {id: $productId})
ON CREATE SET p.name = $productName, p.category = $category
RETURN p.id AS productId;
"""
