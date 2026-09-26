// ==========================================
// NEXUSGRAPH SUPPORT - CYPHER QUERY CATALOG
// All queries use explicit parameter binding ($)
// ==========================================

// 1. Seed Customer and Entitlement
MERGE (c:Customer {email: $email})
ON CREATE SET c.name = $name, c.company = $company
MERGE (p:Product {id: $productId})
ON CREATE SET p.name = $productName
MERGE (c)-[:PURCHASED]->(p)
RETURN c.email AS customerEmail, p.name AS productName;

// 2. Session 1: Create Initial Support Ticket & Memory
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

// 3. Session 2: Retrieve Active Ticket Context
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

// 4. Session 2: Escalate Ticket on Persistent Failure
MATCH (t:SupportTicket {id: $ticketId})
MATCH (o:Outcome {id: $outcomeId})
SET o.status = 'FAILED',
    o.feedback = $feedback,
    o.recordedAt = datetime(),
    t.status = 'ESCALATED',
    t.updatedAt = datetime()
CREATE (r2:Resolution {
    id: $newResolutionId,
    actionName: 'TIER_2_ESCALATION',
    instructions: 'Automated diagnostic snapshot forwarded to Cloud Operations. License reprovisioning queued.',
    tier: 2
})
CREATE (o2:Outcome {
    id: $newOutcomeId,
    status: 'PENDING',
    feedback: 'Ticket queued for engineering review',
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

// 5. Visual Subgraph Inspection for Customer
MATCH (c:Customer {email: $email})
OPTIONAL MATCH (c)-[r1:PURCHASED]->(p:Product)
OPTIONAL MATCH (c)-[r2:OPENED_TICKET]->(t:SupportTicket)
OPTIONAL MATCH (t)-[r3:TARGETS]->(tp:Product)
OPTIONAL MATCH (t)-[r4:EXHIBITS]->(i:Issue)
OPTIONAL MATCH (t)-[r5:ATTEMPTED]->(res:Resolution)
OPTIONAL MATCH (res)-[r6:HAS_OUTCOME]->(out:Outcome)
RETURN c, t, p, tp, i, res, out, r1, r2, r3, r4, r5, r6;

// 6. Reset Customer State
MATCH (c:Customer {email: $email})
OPTIONAL MATCH (c)-[:OPENED_TICKET]->(t:SupportTicket)
OPTIONAL MATCH (t)-[:EXHIBITS]->(i:Issue)
OPTIONAL MATCH (t)-[:ATTEMPTED]->(r:Resolution)
OPTIONAL MATCH (r)-[:HAS_OUTCOME]->(o:Outcome)
OPTIONAL MATCH (t)-[:HAS_INTERACTION]->(int:Interaction)
DETACH DELETE t, i, r, o, int;
