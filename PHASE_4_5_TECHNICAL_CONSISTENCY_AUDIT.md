# PHASE 4.5: TECHNICAL CONSISTENCY AUDIT & FINAL LOCKED SPECIFICATION
## Context-Aware Customer Support Agent (PS-1)

---

# 1. CORRECTIONS MADE

| # | Item Audited | Previous Issue / Contradiction | Final Audited Resolution |
|---|---|---|---|
| **1** | **Product Identity** | `Product` was merged by `id` during seed, but matched by `name` during ticket creation, risking duplicates or mismatched relationships. | **`Product.id` is the canonical identifier everywhere.** The backend resolves any extracted product name to a canonical `Product.id` (`PROD-GDS-01`) before executing Cypher. All queries strictly `MATCH (p:Product {id: $productId})`. |
| **2** | **Active Ticket Retrieval** | Retrieval query used `LIMIT 1`, silently dropping multiple open tickets and hiding potential ambiguity. | **`LIMIT 1` removed from initial fetch.** Backend checks ticket count: `0` $\rightarrow$ New issue flow; `1` $\rightarrow$ Target active ticket; `2+` $\rightarrow$ Triggers deterministic disambiguation asking user to choose between tickets. |
| **3** | **Resolution & Outcome Pairing** | `Resolution` and `Outcome` nodes were collected independently, risking mismatched array index ordering. | **Atomic Traversal Pairing:** Query traverses `(t)-[:ATTEMPTED]->(r:Resolution)-[:HAS_OUTCOME]->(o:Outcome)` and packages `{resolution: r, outcome: o}` as a single bound map before taking the latest pair. |
| **4** | **Customer Identity** | Language implied "identity verification" in a system without real auth. | **Controlled Demo Persona Mapping:** Explicitly declared as a hardcoded demo persona selector (`Alice Chen` $\rightarrow$ `alice@techcorp.io`). Production authentication is officially out of scope. |
| **5** | **Unknown Customer Handling** | Previous plan proposed auto-provisioning unknown customers with default entitlements. | **Strict Fallback:** If `Customer` node does not exist in Neo4j, backend returns a controlled error: `"CUSTOMER_NOT_FOUND. Please click 'Seed Customer' to initialize the demo persona."` No fake entitlements are auto-created. |
| **6** | **State Transition Trigger** | `PENDING → FAILED` risked triggering on any random follow-up message. | **Explicit Feedback Gate:** Outcome mutates to `FAILED` **if and only if** the extraction layer detects explicit failure confirmation (`feedback_type == 'PERSISTENT_FAILURE'`). General questions do not trigger escalation. |
| **7** | **LLM Cypher Generation** | Ambiguity remained whether LLM writes Cypher or backend handles queries. | **100% Pre-compiled Parameterized Cypher:** Zero LLM-generated Cypher. The LLM only extracts structured Pydantic JSON. The backend executes hardcoded parameterized query templates. |
| **8** | **Session Boundary** | Possibility of frontend state bleed between sessions. | **Zero-State Session Reset:** Session Break explicitly unmounts and empties React state. Backend is fully stateless. Session 2 reconstructs 100% of context via Neo4j graph traversal. |

---

# 2. FINAL DATABASE IDENTITY RULES

### Canonical Identifiers:
1. **`:Customer`**: **`email`** (String, Unique Constraint) — e.g., `"alice@techcorp.io"`.
2. **`:Product`**: **`id`** (String, Unique Constraint) — e.g., `"PROD-GDS-01"`.
   - *Backend Mapping:*
     ```python
     PRODUCT_NAME_TO_ID = {
         "graph data science workspace": "PROD-GDS-01",
         "gds workspace": "PROD-GDS-01",
         "gds": "PROD-GDS-01",
         "neo4j aura": "PROD-AURA-01",
         "aura": "PROD-AURA-01",
     }
     DEFAULT_PRODUCT_ID = "PROD-GDS-01"
     ```
3. **`:SupportTicket`**: **`id`** (String, Unique Constraint) — format: `"TK-101"`.
4. **`:Issue`**: **`id`** (String, Unique Constraint) — format: `"ISS-403"`.
5. **`:Resolution`**: **`id`** (String, Unique Constraint) — format: `"RES-SSO"` / `"RES-ESC"`.
6. **`:Outcome`**: **`id`** (String, Unique Constraint) — format: `"OUT-101-1"` / `"OUT-101-2"`.
7. **`:Interaction`**: **`id`** (String, Unique Constraint) — format: `"INT-<timestamp>"`.

---

# 3. FINAL RETRIEVAL RULES

### Multi-Ticket Determination:
```text
Retrieve Active Tickets for Customer ($email)
          │
          ├── Count == 0  ──> ROUTE: New Issue Flow
          │                   (Create Ticket TK-101, Issue, Res 1, Outcome PENDING)
          │
          ├── Count == 1  ──> ROUTE: Ongoing Support Flow
          │                   (Check user feedback -> Mutate PENDING to FAILED -> Escalate)
          │
          └── Count >= 2  ──> ROUTE: Disambiguation Flow
                              (Ask user: "I see 2 open tickets: TK-101 (GDS) and TK-102 (Aura). Which are you following up on?")
```

### Exact Cypher Retrieval Query (Atomic Resolution-Outcome Pairing):
```cypher
MATCH (c:Customer {email: $email})-[:OPENED_TICKET]->(t:SupportTicket)
WHERE t.status IN ['OPEN', 'ESCALATED']
MATCH (t)-[:TARGETS]->(p:Product)
MATCH (t)-[:EXHIBITS]->(i:Issue)
OPTIONAL MATCH (t)-[:ATTEMPTED]->(r:Resolution)-[:HAS_OUTCOME]->(o:Outcome)
WITH t, p, i, r, o
ORDER BY r.tier DESC, o.recordedAt DESC
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
```

---

# 4. FINAL STATE MACHINE

### SupportTicket Lifecycle:
$$\text{(NONE)} \xrightarrow{\text{Session 1: Customer reports issue}} \mathbf{OPEN} \xrightarrow[\text{"It's still not working"}]{\text{Session 2: Explicit failure feedback}} \mathbf{ESCALATED}$$

### Outcome Lifecycle:
$$\text{(NONE)} \xrightarrow{\text{Resolution 1 prescribed}} \mathbf{PENDING} \xrightarrow[\text{"It's still not working"}]{\text{Explicit failure confirmation}} \mathbf{FAILED}$$

### State Transition Policy:
- A transition from `PENDING` to `FAILED` is **gated by intent extraction**:
  - `intent == 'ISSUE_FOLLOWUP'` AND `feedback_type == 'PERSISTENT_FAILURE'` $\implies$ Mutate to `FAILED` and `ESCALATED`.
  - If `intent == 'GENERAL_QUERY'` (e.g., *"What are your support hours?"*) $\implies$ Do **not** mutate ticket or outcome state.

---

# 5. FINAL AGENT BOUNDARIES

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        AGENT ARCHITECTURE MATRIX                       │
├───────────────────────────────────┬────────────────────────────────────┤
│ LLM RESPONSIBILITIES              │ BACKEND RESPONSIBILITIES           │
├───────────────────────────────────┼────────────────────────────────────┤
│ 1. Structured JSON extraction     │ 1. Validate JSON against Pydantic  │
│    (intent, error code, symptom)  │ 2. Map customer persona to email   │
│ 2. Natural language synthesis     │ 3. Resolve Product Name to ID      │
│    grounded strictly in DB facts  │ 4. Execute pre-compiled Cypher     │
│                                   │ 5. Evaluate state machine rules    │
│                                   │ 6. Enforce zero repeating of fixes │
├───────────────────────────────────┼────────────────────────────────────┤
│ FORBIDDEN TO LLM                  │ FORBIDDEN TO BACKEND               │
├───────────────────────────────────┼────────────────────────────────────┤
│ ❌ Generate arbitrary Cypher      │ ❌ Relying on in-memory chat cache │
│ ❌ Directly mutate Neo4j          │ ❌ Auto-provisioning unknown users │
│ ❌ Invent ticket or product IDs   │ ❌ Arbitrary string concatenation  │
│ ❌ Claim external system actions  │    in Cypher queries               │
└───────────────────────────────────┴────────────────────────────────────┘
```

---

# 6. FINAL API BEHAVIOR

### Core Endpoints:

#### 1. `POST /api/chat`
* **Request:** `{ "email": "alice@techcorp.io", "message": "It's still not working.", "session_id": "session-2" }`
* **Flow:**
  1. Check Customer exists in Neo4j. If not $\rightarrow$ HTTP 404: `"Customer not found. Please click 'Seed Customer'."`
  2. Extract intent via LLM (`intent`, `feedback_type`, `symptom`).
  3. Query active tickets via Operation 4.
  4. Evaluate ticket count:
     - `0`: Run Session 1 graph creation (Ticket `TK-101`, Issue `403`, Res 1 `CLEAR_SSO_CACHE`, Outcome `PENDING`).
     - `1` and `feedback_type == 'PERSISTENT_FAILURE'`: Run Session 2 mutation (Outcome `FAILED`, Ticket `ESCALATED`, Res 2 `TIER_2_ESCALATION`, Outcome `PENDING`).
     - `2+`: Return disambiguation response without mutating state.
  5. Grounded LLM response generated from graph state.
  6. Return `ChatResponse` JSON.

#### 2. `GET /api/graph/{email}`
* Returns `{ "nodes": [...], "relationships": [...] }` for the active customer subgraph.

#### 3. `POST /api/demo/seed`
* Pre-seeds `:Customer {email: "alice@techcorp.io", name: "Alice Chen"}` and `:Product {id: "PROD-GDS-01", name: "Graph Data Science Workspace"}`.

#### 4. `POST /api/demo/reset`
* Detaches and deletes tickets, issues, resolutions, outcomes, and interactions for `alice@techcorp.io`.

---

# 7. FINAL SESSION BEHAVIOR

To prove persistent Neo4j memory to the hackathon judges:

1. **Session 1:** User reports issue $\rightarrow$ Neo4j creates graph nodes $\rightarrow$ Agent prescribes Step 1.
2. **Session Break (The Test):**
   - User clicks **"Simulate Session Break"**.
   - Frontend state is completely wiped (`messages = []`).
   - The FastAPI backend holds **zero conversational state** in memory.
3. **Session 2:** User types: `"It's still not working."`
   - Payload has zero chat history.
   - Backend queries Neo4j by customer email, finds `TK-101`, detects `CLEAR_SSO_CACHE`, and immediately knows the exact context.

---

# 8. FINAL CRITICAL DEMO FLOW (3-Minute Sequence)

```text
[0:00 - 0:30] 1. SEED DEMO CUSTOMER
              • Click [1. Seed Customer] -> Graph Inspector displays Alice Chen + GDS Workspace.

[0:30 - 1:15] 2. SESSION 1 (Initial Issue Reporting)
              • Click [2. Send Session 1 Issue] ("My GDS workspace fails with Error 403 on launch").
              • Agent replies: Logs Ticket #TK-101, prescribes clearing SSO cache.
              • Graph Inspector renders: Ticket (OPEN - Yellow), Resolution 1, Outcome (PENDING - Gray).

[1:15 - 1:45] 3. SIMULATE SESSION BREAK
              • Click [3. Simulate Break (Wipe UI)] -> Chat transcript clears completely.
              • Emphasize to judges: "The frontend memory is now completely empty."

[1:45 - 2:30] 4. SESSION 2 (The Vague Return)
              • Click [4. Send 'It's still not working'] (4 words only).
              • Backend queries Neo4j, retrieves active ticket TK-101 and prior fix.
              • Outcome mutates to FAILED (Red ❌). Ticket mutates to ESCALATED (Orange ⚡).
              • Tier-2 Escalation node is added.
              • Agent replies: "Welcome back Alice. I see that clearing your SSO cache didn't resolve Error 403..."

[2:30 - 3:00] 5. CONCLUSION & JUDGING RECAP
              • Point out how the graph physically changed in real-time.
              • Reiterate: Zero customer repetition, zero hallucination, sub-millisecond retrieval.
```

---

# 9. REMAINING RISKS & MITIGATIONS

| Risk | Impact | Deterministic Mitigation |
|---|---|---|
| **AuraDB Network Timeout** | Latency during demo | Python driver connection pooling with keep-alive enabled on app startup. |
| **LLM Output Format Glitch** | Malformed JSON on extraction | Fallback regex: If message contains `"not working"`, default to `intent: 'ISSUE_FOLLOWUP'` and `feedback_type: 'PERSISTENT_FAILURE'`. |
| **Accidental Button Double-Click** | Duplicate queries | Frontend disables buttons during active request loading state. |

---

# 10. FINAL LOCKED SPECIFICATION

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   LOCKED TECHNICAL SPECIFICATION                       │
├────────────────────────────────────────────────────────────────────────┤
│ Architecture:     FastAPI (Backend) + React/Tailwind (Frontend)        │
│ Database:         Neo4j AuraDB (Cloud) via official neo4j Python driver│
│ Extraction:       Gemini Flash (Strict JSON Schema mode)               │
│ Primary Key:      Customer: email | Product: id ('PROD-GDS-01')        │
│ Graph Topology:   Customer -> Ticket -> Product / Issue / Res -> Out   │
│ State Machine:    Ticket (OPEN -> ESCALATED) | Outcome (PENDING -> FAILED)│
│ Cypher Execution: 100% Parameterized Templates (Zero text-to-Cypher)   │
│ Demo Sequence:    5-Button Scripted Flow (Seed -> S1 -> Break -> S2)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

# READY FOR PHASE 5 IMPLEMENTATION
