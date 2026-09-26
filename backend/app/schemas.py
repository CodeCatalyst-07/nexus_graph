from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any

# --- 1. User Chat Input ---
class ChatRequest(BaseModel):
    email: str = Field(..., description="Customer canonical email address, e.g. alice@techcorp.io")
    message: str = Field(..., description="Customer message text")
    session_id: Optional[str] = Field("session-1", description="Session identifier for multi-session simulation")

# --- 2. LLM Extraction Schema ---
class MemoryExtraction(BaseModel):
    intent: Literal["REPORT_NEW_ISSUE", "ISSUE_FOLLOWUP", "GENERAL_QUERY"] = Field(
        ..., description="Classified intent of the user message"
    )
    product_name: Optional[str] = Field(None, description="Identified product name, e.g., 'Graph Data Science Workspace'")
    error_code: Optional[str] = Field(None, description="Numeric or alphanumeric error code, e.g., '403'")
    symptom: Optional[str] = Field(None, description="Description of the failure or symptom observed")
    feedback_type: Optional[Literal["PERSISTENT_FAILURE", "RESOLVED", "NEUTRAL"]] = Field(
        "NEUTRAL", description="Explicit feedback regarding whether a previous fix worked"
    )

# --- 3. Retrieval Result Schema ---
class ActiveTicketContext(BaseModel):
    ticket_id: str
    ticket_status: str
    product_id: str
    product_name: str
    error_code: str
    issue_description: str
    resolution_id: Optional[str] = None
    last_action_name: Optional[str] = None
    last_instructions: Optional[str] = None
    outcome_id: Optional[str] = None
    last_outcome_status: Optional[str] = None
    ticket_updated_at: Optional[str] = None

# --- 4. Chat Response Schema ---
class ChatResponse(BaseModel):
    reply: str
    ticket_id: Optional[str] = None
    ticket_status: Optional[str] = None
    action_taken: str
    memory_updated: bool = False
    retrieved_context: Optional[ActiveTicketContext] = None
    executed_cypher_summary: str

# --- 5. Graph Inspector Schemas ---
class GraphNode(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any]

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    properties: Optional[Dict[str, Any]] = None

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# --- 6. Demo Control Schemas ---
class DemoCustomerRequest(BaseModel):
    email: Optional[str] = "alice@techcorp.io"

class GenericStatusResponse(BaseModel):
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None
