# NexusGraph Support 🚀
### Context-Aware Customer Support Agent with Neo4j Episodic & Knowledge Memory
**Built for the Neo4j × hackFront India Agent Memory Build Sprint Pune**

[![Neo4j](https://img.shields.io/badge/Database-Neo4j%20AuraDB-008CC1?logo=neo4j&logoColor=white)](https://neo4j.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61DAFB?logo=react&logoColor=black)](https://vitejs.dev/)
[![Groq](https://img.shields.io/badge/Inference-Groq%20LPU%20(~150ms)-F55036?logo=groq&logoColor=white)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🌟 Executive Summary

**NexusGraph Support** is an enterprise AI support agent powered by a stateful **Neo4j Knowledge and Episodic Memory Graph**. It completely eliminates the customer pain of repeating context across sessions.

When a returning customer sends a terse follow-up after an hours-long break:
> *"It's still not working."*

NexusGraph does **not** rely on bloated transcript windows or fuzzy vector embeddings. Instead, it:
1. Queries the customer's active subgraph in Neo4j via Cypher.
2. Identifies the open ticket (`#TK-101`), the affected product (*Graph Data Science Workspace*), and the active diagnostic step (`CLEAR_SSO_CACHE`).
3. Explicitly mutates the prior outcome to **`FAILED`** and atomically transitions the ticket to **`ESCALATED`**.
4. Dispatches the issue directly to Tier-2 engineering—all with **zero conversational amnesia** and **zero hallucination**.

---

## 🧠 Why Neo4j? (Graph Thinking vs. Relational/Vector)

| Capability | Vector DB (RAG) | Relational SQL | Neo4j Graph Memory (Ours) |
|---|---|---|---|
| **Multi-Hop Traversal** | Cannot join relations; fuzzy text similarity only. | Requires expensive 6-table `JOIN` operations. | **Native O(1) index-free adjacency** across entities. |
| **Stateful Lifecycle** | Cannot track whether an outcome succeeded or failed. | Requires rigid tables with brittle foreign key cascades. | **Explicit Outcome nodes** (`status: 'PENDING' \| 'FAILED' \| 'SUCCESS'`). |
| **Context Window Hygiene** | Dumps raw transcript chunks into the prompt. | Manual query building with high schema overhead. | **Extracts only the 2-hop active subgraph**, minimizing prompt tokens. |
| **Idempotency & Grounding** | High hallucination risk during state updates. | ACID compliant, but hard to represent evolving causal chains. | **Deterministic Cypher transactions** with guaranteed consistency. |

---

## 🏗️ Architecture & Memory Pipeline

```
  [ Customer Message ]
           │
           ▼
  ┌────────────────────────────────────────────────────────┐
  │ 1. Multi-Tier Hybrid Extraction                        │
  │    • Tier 1: Groq LPU (~150ms, JSON Mode)              │
  │    • Tier 2: Google Gemini (Secondary Fallback)        │
  │    • Tier 3: Deterministic Rule-Based Fallback         │
  └────────────────────────┬───────────────────────────────┘
                           │ (intent, product, error_code, feedback)
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │ 2. Neo4j Graph Memory Orchestrator                     │
  │    • Check Customer & Entitlement Graph                │
  │    • Traverse Active Ticket & Resolution Chain         │
  │    • Mutate Outcome State (PENDING -> FAILED)          │
  │    • Atomic Escalation (OPEN -> ESCALATED)             │
  └────────────────────────┬───────────────────────────────┘
                           │ (grounded subgraph context)
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │ 3. Dual Output Generation                              │
  │    ├─ Customer Chat: Grounded, Contextual Reply        │
  │    └─ Graph Inspector: Live SVG Subgraph Visualization │
  └────────────────────────────────────────────────────────┘
```

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
                                                                               (:Outcome {status: 'PENDING'|'FAILED'|'SUCCESS'})
```

### Node Types
- `(:Customer)`: Enterprise user identity (indexed on unique `email`).
- `(:Product)`: Catalog of provisioned cloud products and workspaces.
- `(:SupportTicket)`: State machine node (`OPEN`, `ESCALATED`, `RESOLVED`).
- `(:Issue)`: Specific operational anomaly (error code, observed symptom).
- `(:Resolution)`: Prescribed troubleshooting actions and diagnostic steps.
- `(:Outcome)`: Explicit validation tracking (`PENDING`, `FAILED`, `SUCCESS`).
- `(:Interaction)`: Complete audit trail of customer queries and agent responses.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic v2, Uvicorn, HTTPX.
- **Graph Database:** Neo4j AuraDB (Enterprise Cloud), official `neo4j` Python driver, binary Bolt protocol (`neo4j+s://`).
- **Inference Engines:**
  - **Groq LPU API** (`openai/gpt-oss-20b`): Ultra-fast intent & entity extraction (~150ms) and dynamic replies.
  - **Google Gemini API** (`gemini-2.5-flash`): Reliable secondary LLM fallback.
  - **Deterministic Heuristic Engine**: Zero-dependency offline rule fallback.
- **Frontend:** React 18, Vite, Tailwind CSS, Lucide React, Custom Interactive SVG Graph Explorer.
- **Deployment:** Render (Cloud Backend), Vercel (Frontend).

---

## ⚡ API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Main conversational endpoint; extracts intent, traverses Neo4j, and returns grounded reply. |
| `GET` | `/api/graph/{email}` | Retrieves the complete active episodic memory subgraph for visual rendering. |
| `POST` | `/api/demo/seed` | Seeds the baseline customer persona (`Alice Chen`) and product catalog in Neo4j. |
| `POST` | `/api/demo/reset` | Resets all demo tickets, issues, resolutions, and outcomes for a clean test state. |
| `GET` | `/` | Root health check verifying backend status and active Neo4j connectivity. |

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Free Neo4j AuraDB instance (or local Neo4j Desktop)

### 1. Environment Configuration
Clone the repository and copy the sample environment file:
```bash
git clone https://github.com/CodeCatalyst-07/nexus_graph.git
cd nexus_graph
cp .env.example backend/.env
```
Fill in your credentials in `backend/.env`:
```env
NEO4J_URI=neo4j+s://<your-db-id>.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-neo4j-password>

# Optional API Keys (defaults to deterministic heuristics if omitted)
GROQ_API_KEY=<your-groq-api-key>
GEMINI_API_KEY=<your-gemini-api-key>
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start backend server
python3 -m uvicorn app.main:app --reload --port 8001
```
The API will be live at `http://localhost:8001`. Interactive OpenAPI docs are at `http://localhost:8001/docs`.

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🏆 Hackathon Judging Criteria Alignment

| Criterion | Weight | How NexusGraph Support Delivers |
|---|---|---|
| **Neo4j & Graph Thinking** | **25%** | Native graph traversal replaces 6-table relational SQL JOINs and avoids vector search amnesia. Nodes and relationships explicitly model state evolution. |
| **Agent Memory & Retrieval** | **25%** | Demonstrates cross-session episodic memory. The agent recovers product, ticket, and failed resolution from a 4-word prompt after chat history is wiped. |
| **Problem-Solution Fit** | **20%** | Solves the universal pain point of support amnesia and Groundhog Day troubleshooting. |
| **Working Implementation** | **15%** | Full-stack FastAPI + React app communicating live over binary Bolt protocol with Neo4j AuraDB. |
| **Demo & UX** | **10%** | Dual-pane layout featuring real-time interactive SVG graph rendering and seamless one-click workflow simulation controls. |
| **Innovation & Creativity** | **5%** | Resolution Failure Awareness: tracking the outcome of past recommendations to dynamically guide future escalation logic. |
