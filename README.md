# NexusGraph Support 🚀
### Context-Aware Customer Support Agent with Neo4j Agent Memory
**Built for the Neo4j × hackFront India Agent Memory Build Sprint Pune**

---

## 🌟 Executive Summary
**NexusGraph Support** is an AI customer support agent that utilizes a stateful **Neo4j Knowledge and Episodic Memory Graph** to completely eliminate repetitive customer explanations. When a returning customer provides a vague follow-up such as:

> *"It's still not working."*

NexusGraph queries the active customer subgraph in Neo4j, detects the exact product (*Graph Data Science Workspace*), diagnoses the error (*403 Forbidden*), identifies the previously attempted troubleshooting step (*Clear SSO Cache*), marks that previous resolution as **FAILED**, and escalates the ticket to **Tier-2**—all without asking the user to repeat a single detail.

---

## 🧠 Why Neo4j? (Graph Thinking vs. Relational/Vector)
1. **Multi-Hop Relational Context:** Resolving a vague query requires traversing `(Customer) -> (SupportTicket) -> (Product) + (Issue) + (Resolution) -> (Outcome)`. In relational SQL, this demands complex 6-table joins. In Neo4j, this is a native, pointer-hop graph traversal.
2. **Stateful Graph Mutation:** Vector databases perform fuzzy similarity searches on raw unstructured text and cannot determine whether a ticket is `OPEN` or `RESOLVED`, nor whether a troubleshooting step succeeded or failed. Neo4j models resolution outcomes as explicit graph nodes (`Outcome {status: 'FAILED'}`), guaranteeing deterministic state reasoning without hallucinations.
3. **Context Isolation:** Instead of bloating the prompt with raw transcripts, the system extracts the exact 2-hop active subgraph and injects only this focused context into the agent.

---

## 📊 Graph Schema & Topology
```text
                     (:Customer {email, name, company})
                                     │
               ┌─────────────────────┴─────────────────────┐
               │ [:PURCHASED]                              │ [:OPENED_TICKET]
               ▼                                           ▼
      (:Product {id, name, version})              (:SupportTicket {id, status, priority})
               ▲                                           │
               │ [:TARGETS]                                ├───────────────────────┬───────────────────────┐
               │                                           │ [:EXHIBITS]           │ [:ATTEMPTED]          │ [:HAS_INTERACTION]
               │                                           ▼                       ▼                       ▼
               └────────────────────────────────── (:Issue {errorCode, desc})   (:Resolution)        (:Interaction)
                                                                                   │
                                                                                   │ [:HAS_OUTCOME]
                                                                                   ▼
                                                                               (:Outcome {status: 'PENDING'|'FAILED'})
```

---

## 🛠️ Tech Stack
- **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons, Custom Interactive SVG Graph Inspector.
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, Official `neo4j` Python driver.
- **Database:** Neo4j AuraDB (Cloud) over encrypted binary Bolt protocol.
- **LLM Engine:** Gemini / Grounded State Machine Synthesis.

---

## 🚀 Quickstart & Setup

### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload --port 8001
```
Backend API will be running at `http://localhost:8001`. Automatic OpenAPI documentation is available at `http://localhost:8001/docs`.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🎬 3-Minute Live Demo Pitch Sequence

Use the **1-Click Scripted Demo Controls** in the top-right panel to execute the winning pitch:

1. **Step 1: [Seed Customer]**
   - Click button.
   - Pre-seeds `:Customer (Alice Chen)` and `:Product (Graph Data Science Workspace)` in Neo4j.
   - Graph Inspector immediately renders Alice connected to the GDS product.
2. **Step 2: [Send S1 Issue]**
   - Click button.
   - Simulates Alice reporting: *"Hi, my Graph Data Science workspace is failing with Error 403 on launch."*
   - Agent logs Ticket `#TK-101 (OPEN)`, diagnoses Error 403, and prescribes clearing the SSO cache.
   - Graph updates in real-time with Ticket, Issue, Resolution 1, and Outcome `PENDING`.
3. **Step 3: [Simulate Break]**
   - Click button.
   - Completely wipes the frontend conversation messages (`messages = []`).
   - Demonstrates to judges that the system holds **zero in-memory conversation state**.
4. **Step 4: [Send S2 Return ("It's still not working")]**
   - Click button.
   - Sends the 4-word follow-up with zero chat history.
   - Backend queries Neo4j, retrieves Ticket `#TK-101`, marks Outcome 1 as **FAILED ❌**, updates Ticket to **ESCALATED ⚡**, and creates a Tier-2 resolution.
   - Agent responds: *"Welcome back Alice. I see that clearing your SSO cache didn't resolve Error 403 on your GDS Workspace. Since Tier-1 troubleshooting failed, I have escalated Ticket #TK-101 in the support workflow for Tier-2 review."*
5. **Step 5: [Reset Canvas]**
   - Click button to wipe demo ticket state for a clean re-run.

---

## 🏆 Hackathon Judging Criteria Alignment

| Criterion | Weight | How NexusGraph Support Delivers |
|---|---|---|
| **Neo4j & Graph Thinking** | **25%** | Native graph traversal replaces 6-table relational SQL JOINs and avoids vector search amnesia. Nodes and relationships explicitly model state evolution. |
| **Agent Memory & Retrieval** | **25%** | Demonstrates cross-session episodic memory. The agent recovers product, ticket, and failed resolution from a 4-word prompt after chat history is wiped. |
| **Problem-Solution Fit** | **20%** | Solves the universal pain point of support amnesia and Groundhog Day troubleshooting. |
| **Working Implementation** | **15%** | Full-stack FastAPI + React app communicating live over binary Bolt protocol with Neo4j AuraDB. |
| **Demo & UX** | **10%** | Dual-pane layout featuring real-time interactive SVG graph rendering and 1-click demo controls for a flawless 3-minute pitch. |
| **Innovation & Creativity** | **5%** | Resolution Failure Awareness: tracking the outcome of past recommendations to dynamically guide future escalation logic. |
