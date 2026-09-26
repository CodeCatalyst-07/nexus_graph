// Constraints for NexusGraph Support Memory Graph
CREATE CONSTRAINT customer_email_unique IF NOT EXISTS
FOR (c:Customer) REQUIRE c.email IS UNIQUE;

CREATE CONSTRAINT product_id_unique IF NOT EXISTS
FOR (p:Product) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT ticket_id_unique IF NOT EXISTS
FOR (t:SupportTicket) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT issue_id_unique IF NOT EXISTS
FOR (i:Issue) REQUIRE i.id IS UNIQUE;

CREATE CONSTRAINT resolution_id_unique IF NOT EXISTS
FOR (r:Resolution) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT outcome_id_unique IF NOT EXISTS
FOR (o:Outcome) REQUIRE o.id IS UNIQUE;

CREATE CONSTRAINT interaction_id_unique IF NOT EXISTS
FOR (n:Interaction) REQUIRE n.id IS UNIQUE;
