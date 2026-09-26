from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging

from app.schemas import (
    ChatRequest,
    ChatResponse,
    GraphResponse,
    GraphNode,
    GraphEdge,
    DemoCustomerRequest,
    GenericStatusResponse
)
from app.agent import handle_chat_message
from app.database import run_query
import app.cypher_library as cypher

logger = logging.getLogger("nexusgraph.routes")
router = APIRouter(prefix="/api")

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """Primary chat endpoint executing deterministic support memory lifecycle."""
    try:
        response = handle_chat_message(
            email=req.email,
            message=req.message,
            session_id=req.session_id or "session-1"
        )
        return response
    except Exception as e:
        logger.error(f"Error in chat_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal agent processing error: {str(e)}")

@router.get("/graph/{email}", response_model=GraphResponse)
def get_graph_endpoint(email: str):
    """Returns active customer subgraph formatted for visual inspection."""
    try:
        records = run_query(cypher.GET_CUSTOMER_SUBGRAPH, {"email": email})
        nodes_dict: Dict[str, GraphNode] = {}
        edges_list: List[GraphEdge] = []
        edge_keys = set()

        for r in records:
            # 1. Customer
            c = r.get("c")
            if c:
                c_id = c.get("email") or email
                if c_id not in nodes_dict:
                    nodes_dict[c_id] = GraphNode(
                        id=c_id,
                        label="Customer",
                        properties={"name": c.get("name", "Alice Chen"), "email": c_id}
                    )

            # 2. Products (from purchased p and targeted tp)
            for prod_node in [r.get("p"), r.get("tp")]:
                if prod_node:
                    p_id = prod_node.get("id")
                    if p_id and p_id not in nodes_dict:
                        nodes_dict[p_id] = GraphNode(
                            id=p_id,
                            label="Product",
                            properties={"name": prod_node.get("name", ""), "category": prod_node.get("category", "")}
                        )

            # 3. Ticket
            t = r.get("t")
            if t:
                t_id = t.get("id") or ""
                if t_id and t_id not in nodes_dict:
                    nodes_dict[t_id] = GraphNode(
                        id=t_id,
                        label="SupportTicket",
                        properties={
                            "status": t.get("status", "OPEN"),
                            "priority": t.get("priority", "HIGH"),
                            "id": t_id
                        }
                    )

            # 4. Issue
            i = r.get("i")
            if i:
                i_id = i.get("id") or ""
                if i_id and i_id not in nodes_dict:
                    nodes_dict[i_id] = GraphNode(
                        id=i_id,
                        label="Issue",
                        properties={"errorCode": i.get("errorCode", "403"), "description": i.get("description", "")}
                    )

            # 5. Resolution
            res = r.get("res")
            if res:
                res_id = res.get("id") or ""
                if res_id and res_id not in nodes_dict:
                    nodes_dict[res_id] = GraphNode(
                        id=res_id,
                        label="Resolution",
                        properties={"actionName": res.get("actionName", ""), "tier": res.get("tier", 1)}
                    )

            # 6. Outcome
            out = r.get("out")
            if out:
                out_id = out.get("id") or ""
                if out_id and out_id not in nodes_dict:
                    nodes_dict[out_id] = GraphNode(
                        id=out_id,
                        label="Outcome",
                        properties={"status": out.get("status", "PENDING"), "feedback": out.get("feedback", "")}
                    )

            # Relationships: strictly verified by relationship presence
            p = r.get("p")
            tp = r.get("tp")
            r1 = r.get("r1")
            r2 = r.get("r2")
            r3 = r.get("r3")
            r4 = r.get("r4")
            r5 = r.get("r5")
            r6 = r.get("r6")

            if r1 and c and p:
                e_key = f"{c.get('email')}->PURCHASED->{p.get('id')}"
                if e_key not in edge_keys:
                    edge_keys.add(e_key)
                    edges_list.append(GraphEdge(
                        id=e_key,
                        source=c.get("email"),
                        target=p.get("id"),
                        type="PURCHASED"
                    ))

            if r2 and c and t:
                e_key = f"{c.get('email')}->OPENED_TICKET->{t.get('id')}"
                if e_key not in edge_keys:
                    edge_keys.add(e_key)
                    edges_list.append(GraphEdge(
                        id=e_key,
                        source=c.get("email"),
                        target=t.get("id"),
                        type="OPENED_TICKET"
                    ))

            if r3 and t and tp:
                e_key = f"{t.get('id')}->TARGETS->{tp.get('id')}"
                if e_key not in edge_keys:
                    edge_keys.add(e_key)
                    edges_list.append(GraphEdge(
                        id=e_key,
                        source=t.get("id"),
                        target=tp.get("id"),
                        type="TARGETS"
                    ))

            if r4 and t and i:
                e_key = f"{t.get('id')}->EXHIBITS->{i.get('id')}"
                if e_key not in edge_keys:
                    edge_keys.add(e_key)
                    edges_list.append(GraphEdge(
                        id=e_key,
                        source=t.get("id"),
                        target=i.get("id"),
                        type="EXHIBITS"
                    ))

            if r5 and t and res:
                e_key = f"{t.get('id')}->ATTEMPTED->{res.get('id')}"
                if e_key not in edge_keys:
                    edge_keys.add(e_key)
                    edges_list.append(GraphEdge(
                        id=e_key,
                        source=t.get("id"),
                        target=res.get("id"),
                        type="ATTEMPTED"
                    ))

            if r6 and res and out:
                e_key = f"{res.get('id')}->HAS_OUTCOME->{out.get('id')}"
                if e_key not in edge_keys:
                    edge_keys.add(e_key)
                    edges_list.append(GraphEdge(
                        id=e_key,
                        source=res.get("id"),
                        target=out.get("id"),
                        type="HAS_OUTCOME"
                    ))

        return GraphResponse(nodes=list(nodes_dict.values()), edges=edges_list)
    except Exception as e:
        logger.error(f"Error fetching graph: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database graph fetch error: {str(e)}")

@router.post("/demo/seed", response_model=GenericStatusResponse)
def seed_demo_endpoint(req: DemoCustomerRequest):
    """Idempotently seeds demo customer Alice Chen and product entitlement."""
    email = req.email or "alice@techcorp.io"
    try:
        run_query(cypher.SEED_CUSTOMER_PRODUCT, {
            "email": email,
            "name": "Alice Chen",
            "company": "TechCorp Global",
            "productId": "PROD-GDS-01",
            "productName": "Graph Data Science Workspace",
            "category": "Cloud Graph Compute"
        })
        return GenericStatusResponse(
            status="SEEDED",
            message=f"Customer '{email}' and product 'PROD-GDS-01' seeded into Neo4j.",
            details={"customer": "Alice Chen", "product": "Graph Data Science Workspace"}
        )
    except Exception as e:
        logger.error(f"Error seeding demo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to seed demo customer: {str(e)}")

@router.post("/demo/reset", response_model=GenericStatusResponse)
def reset_demo_endpoint(req: DemoCustomerRequest):
    """Clears tickets, issues, resolutions, outcomes, and interactions for demo customer."""
    email = req.email or "alice@techcorp.io"
    try:
        run_query(cypher.RESET_DEMO_STATE, {"email": email})
        return GenericStatusResponse(
            status="RESET_COMPLETE",
            message=f"All tickets and outcomes cleared for customer '{email}'. Customer and entitlement preserved.",
            details={"email": email}
        )
    except Exception as e:
        logger.error(f"Error resetting demo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reset demo state: {str(e)}")
