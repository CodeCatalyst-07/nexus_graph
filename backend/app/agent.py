import re
import uuid
import logging
import json
from typing import Optional, Dict, Any, Tuple, List
import httpx

from app.schemas import MemoryExtraction, ActiveTicketContext, ChatResponse
from app.config import GEMINI_API_KEY, LLM_MODEL, GROQ_API_KEY, GROQ_MODEL
from app.database import run_query
import app.cypher_library as cypher

logger = logging.getLogger("nexusgraph.agent")

# --- Canonical Product Catalog (Phase 4.6 Locked Specification) ---
KNOWN_PRODUCTS = {
    "PROD-GDS-01": {
        "name": "Graph Data Science Workspace",
        "category": "Cloud Graph Compute",
        "aliases": ["graph data science workspace", "gds workspace", "gds", "graph data science", "gds module"]
    },
    "PROD-AURA-01": {
        "name": "Neo4j AuraDB Enterprise",
        "category": "Managed Cloud Database",
        "aliases": ["neo4j auradb enterprise", "auradb", "aura", "neo4j aura"]
    },
    "PROD-PY-01": {
        "name": "Python Application Driver",
        "category": "Client Driver & SDK",
        "aliases": ["python application driver", "python course", "python driver", "python sdk", "python"]
    }
}

DEFAULT_DIAGNOSTICS = {
    "PROD-GDS-01": {
        "actionName": "CLEAR_SSO_CACHE",
        "instructions": "Clear browser session cache and re-authenticate via SSO."
    },
    "PROD-PY-01": {
        "actionName": "UPGRADE_DRIVER_SDK",
        "instructions": "Verify neo4j driver version >= 5.0 and re-check connection URI protocol."
    },
    "PROD-AURA-01": {
        "actionName": "VERIFY_IP_ALLOWLIST",
        "instructions": "Check AuraDB console network settings and ensure your client IP is allowed."
    }
}

def resolve_product(extracted_name: Optional[str]) -> Optional[Tuple[str, str, str]]:
    """
    Resolves extracted product text to (product_id, canonical_name, category) without guessing.
    Returns None if the product cannot be deterministically resolved.
    """
    if not extracted_name:
        return None
    cleaned = extracted_name.strip().lower()
    for prod_id, meta in KNOWN_PRODUCTS.items():
        if cleaned == meta["name"].lower() or any(alias in cleaned for alias in meta["aliases"]):
            return prod_id, meta["name"], meta["category"]
    return None

def extract_intent_and_entities_heuristic(message: str) -> MemoryExtraction:
    """
    Deterministic regex-based extraction engine.
    Guarantees zero latency, zero hallucination, and 100% demo reliability.
    """
    msg_lower = message.lower().strip()

    # 1. Feedback Detection (Using word boundaries to avoid substring false positives)
    failure_patterns = [
        r"\bstill\s+not\s+working\b",
        r"\bnot\s+working\b",
        r"\bstill\s+(fails?|failing|broken|showing|persists?)\b",
        r"\bdidn'?t\s+(work|help|fix)\b",
        r"\bsame\s+(problem|issue)\b",
        r"\bissue\s+persists\b",
        r"\bpersists?\b",
        r"\bnot\s+resolved\b",
        r"\bstill\s+busted\b",
        r"\bhasn'?t\s+changed\b"
    ]
    resolved_patterns = [
        r"\bit\s+worked\b",
        r"\bfixed\s+now\b",
        r"\bissue\s+resolved\b",
        r"\bworking\s+now\b",
        r"\ball\s+good\b",
        r"\bsolved\b",
        r"\bresolved\b",
        r"\bthanks\s+it\s+works\b",
        r"\bproblem\s+is\s+fixed\b"
    ]

    feedback = "NEUTRAL"
    if any(re.search(pat, msg_lower) for pat in failure_patterns):
        feedback = "PERSISTENT_FAILURE"
    elif any(re.search(pat, msg_lower) for pat in resolved_patterns):
        feedback = "RESOLVED"

    # 2. Product Detection
    product_name = None
    if re.search(r"\b(gds|graph\s+data\s+science)\b", msg_lower):
        product_name = "Graph Data Science Workspace"
    elif re.search(r"\b(aura|auradb)\b", msg_lower):
        product_name = "Neo4j AuraDB Enterprise"
    elif re.search(r"\b(python|python\s+course|python\s+driver|python\s+sdk)\b", msg_lower):
        product_name = "Python Application Driver"
    elif re.search(r"\bgds\s+workspace\b", msg_lower):
        product_name = "Graph Data Science Workspace"

    # 3. Error Code Extraction
    error_code = None
    err_match = re.search(r"\b(40[0-9]|50[0-9]|ERR-[A-Z0-9]+)\b", message, re.IGNORECASE)
    if err_match:
        error_code = err_match.group(1).upper()
    elif "forbidden" in msg_lower:
        error_code = "403"

    # 4. Intent Classification
    # Ticket status inquiry pattern (Case D)
    is_status_inquiry = bool(
        re.search(r"\b(status|progress|update)\b", msg_lower) and
        re.search(r"\bticket\b", msg_lower)
    )

    # Ambiguous "another problem" pattern without product (Case E)
    is_ambiguous_followup = bool(
        re.search(r"\b(another\s+(problem|issue)|different\s+(problem|issue)|new\s+problem)\b", msg_lower) and
        not product_name
    )

    if is_status_inquiry:
        intent = "GENERAL_QUERY"
    elif feedback in ["PERSISTENT_FAILURE", "RESOLVED"]:
        intent = "ISSUE_FOLLOWUP"
    elif is_ambiguous_followup:
        intent = "ISSUE_FOLLOWUP"
    elif product_name and re.search(r"\b(problem|error|fails?|failure|broken|cannot|can'?t|issue)\b", msg_lower):
        intent = "REPORT_NEW_ISSUE"
    elif re.search(r"\b(fails?\s+with\s+error|error\s+403|cannot\s+launch|can'?t\s+launch|forbidden|report\s+new\s+issue|new\s+issue)\b", msg_lower):
        intent = "REPORT_NEW_ISSUE"
    elif re.search(r"\b(what|who|where|how|when|can\s+you|help|support\s+hours|hours|pricing|contact)\b", msg_lower):
        intent = "GENERAL_QUERY"
    elif re.search(r"\b(working|it|this|that|persists?)\b", msg_lower):
        intent = "ISSUE_FOLLOWUP"
    else:
        intent = "GENERAL_QUERY"

    symptom = (
        f"Workspace launch failure with error {error_code}" if error_code
        else "Operational failure reported"
    )

    return MemoryExtraction(
        intent=intent,
        product_name=product_name,
        error_code=error_code,
        symptom=symptom,
        feedback_type=feedback
    )

def extract_with_groq_if_available(message: str) -> Optional[MemoryExtraction]:
    """
    Ultra-fast structured JSON extraction via Groq API (80-150ms).
    Uses JSON mode to guarantee schema compliance.
    """
    if not GROQ_API_KEY:
        return None

    system_prompt = """You are an intent and entity extraction engine for enterprise IT support.
Analyze the user message and return strictly valid JSON matching this schema:
{
  "intent": "REPORT_NEW_ISSUE" | "ISSUE_FOLLOWUP" | "GENERAL_QUERY",
  "product_name": "Graph Data Science Workspace" | "Neo4j AuraDB Enterprise" | "Python Application Driver" | null,
  "error_code": string | null,
  "symptom": string | null,
  "feedback_type": "PERSISTENT_FAILURE" | "RESOLVED" | "NEUTRAL"
}
Rules:
- "still not working", "still failing", "persists", "didn't help" -> feedback_type: "PERSISTENT_FAILURE", intent: "ISSUE_FOLLOWUP".
- "fixed now", "it worked" -> feedback_type: "RESOLVED", intent: "ISSUE_FOLLOWUP".
- Reporting a new failure on a named product -> intent: "REPORT_NEW_ISSUE".
- Inquiring about support hours or general info -> intent: "GENERAL_QUERY"."""

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        with httpx.Client(timeout=3.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["choices"][0]["message"]["content"]
                parsed = json.loads(raw_text)
                return MemoryExtraction(**parsed)
    except Exception as e:
        logger.warning(f"Groq API extraction failed/timed out: {e}. Falling back to next engine.")

    return None

def generate_groq_reply(prompt: str, system_prompt: str = "", max_tokens: int = 300) -> Optional[str]:
    """
    Ultra-fast dynamic conversational reply via Groq LPU API (<250ms).
    """
    if not GROQ_API_KEY:
        return None

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": max_tokens
        }
        with httpx.Client(timeout=3.5) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                if content and content.strip():
                    return content.strip()
    except Exception as e:
        logger.warning(f"Groq conversational reply failed/timed out: {e}")

    return None

def generate_gemini_reply(prompt: str, system_prompt: str = "") -> Optional[str]:
    """Fallback conversational reply using Gemini if Groq is unavailable."""
    if not GEMINI_API_KEY:
        return None
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 300
            }
        }
        with httpx.Client(timeout=4.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.warning(f"Gemini reply generation failed: {e}")
    return None

def generate_dynamic_reply(prompt: str, system_prompt: str = "") -> Optional[str]:
    """Prioritizes Groq API for rapid sub-second generation, falls back to Gemini."""
    groq_reply = generate_groq_reply(prompt, system_prompt)
    if groq_reply:
        logger.info("Conversational reply generated by Groq LPU API")
        return groq_reply
    gemini_reply = generate_gemini_reply(prompt, system_prompt)
    if gemini_reply:
        logger.info("Conversational reply generated by Gemini API")
        return gemini_reply
    return None

def extract_with_gemini_if_available(message: str) -> Optional[MemoryExtraction]:
    """
    Attempts structured JSON extraction via Gemini API if an API key is available.
    Falls back gracefully to the deterministic heuristic engine if unavailable or unresponsive.
    """
    if not GEMINI_API_KEY:
        return None

    prompt = f"""You are an intent and entity extraction engine for an enterprise IT support system.
Analyze the user message and extract:
1. intent: Exactly one of ["REPORT_NEW_ISSUE", "ISSUE_FOLLOWUP", "GENERAL_QUERY"]
2. product_name: Exactly one of ["Graph Data Science Workspace", "Neo4j AuraDB Enterprise", "Python Application Driver"] or null if unmentioned.
3. error_code: Alphanumeric error code (e.g. "403") or null.
4. symptom: Brief description of the issue or null.
5. feedback_type: Exactly one of ["PERSISTENT_FAILURE", "RESOLVED", "NEUTRAL"].

Rules:
- "still not working", "still failing", "persists", "didn't help" -> feedback_type: "PERSISTENT_FAILURE", intent: "ISSUE_FOLLOWUP".
- "fixed now", "it worked" -> feedback_type: "RESOLVED", intent: "ISSUE_FOLLOWUP".
- Reporting a new failure on a named product -> intent: "REPORT_NEW_ISSUE".
- Inquiring about support hours or general info -> intent: "GENERAL_QUERY".

Return strictly valid JSON matching this schema:
{{
  "intent": "...",
  "product_name": null,
  "error_code": null,
  "symptom": null,
  "feedback_type": "..."
}}

User message: "{message}"
"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }
        with httpx.Client(timeout=4.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(raw_text)
                return MemoryExtraction(**parsed)
    except Exception as e:
        logger.warning(f"Gemini API extraction failed/timed out: {e}. Falling back to deterministic engine.")

    return None

def extract_intent_and_entities(message: str) -> MemoryExtraction:
    """Three-tier extraction: Groq (ultra-fast LPU) -> Gemini -> Deterministic Heuristic."""
    groq_result = extract_with_groq_if_available(message)
    if groq_result:
        logger.info("Structured extraction powered by Groq LPU API")
        return groq_result

    gemini_result = extract_with_gemini_if_available(message)
    if gemini_result:
        logger.info("Structured extraction powered by Gemini API")
        return gemini_result

    logger.info("Structured extraction powered by Deterministic Heuristic Engine")
    return extract_intent_and_entities_heuristic(message)

def retrieve_active_tickets(email: str) -> List[ActiveTicketContext]:
    """Deterministically queries Neo4j for open/escalated tickets with atomic resolution+outcome pairing."""
    results = run_query(cypher.GET_ACTIVE_TICKETS, {"email": email})
    tickets = []
    for r in results:
        tickets.append(ActiveTicketContext(
            ticket_id=r.get("ticketId") or "",
            ticket_status=r.get("ticketStatus") or "OPEN",
            product_id=r.get("productId") or "",
            product_name=r.get("productName") or "",
            error_code=r.get("errorCode") or "",
            issue_description=r.get("issueDescription") or "",
            resolution_id=r.get("resolutionId"),
            last_action_name=r.get("lastActionName"),
            last_instructions=r.get("lastInstructions"),
            outcome_id=r.get("outcomeId"),
            last_outcome_status=r.get("lastOutcomeStatus"),
            ticket_updated_at=str(r.get("ticketUpdatedAt")) if r.get("ticketUpdatedAt") else None
        ))
    return tickets

def handle_chat_message(email: str, message: str, session_id: str) -> ChatResponse:
    """
    Main Agent Orchestration Pipeline:
    1. Verify Customer exists in Neo4j.
    2. Extract intent, feedback, product, error code.
    3. Route according to Phase 4.6 Locked Specification:
       - Case D / General Query: Zero mutation.
       - Case E / Ambiguous follow-up: Clarification requested without mutation.
       - Route B: REPORT_NEW_ISSUE -> Idempotent check, create ticket and diagnostic memory.
       - Route C: ISSUE_FOLLOWUP -> Context retrieval, atomic state mutation on failure.
    """
    # 1. Customer Verification
    customer_records = run_query(cypher.CHECK_CUSTOMER_EXISTS, {"email": email})
    if not customer_records:
        return ChatResponse(
            reply="Customer record not found. Please click '[1. Seed Customer]' to initialize the demo persona.",
            action_taken="CUSTOMER_NOT_FOUND_ERROR",
            memory_updated=False,
            retrieved_context=None,
            executed_cypher_summary="MATCH (c:Customer {email: $email}) -> No record found"
        )
    customer = customer_records[0]
    customer_name = customer.get("name", "Alice Chen")

    # 2. Extract Intent and Entities
    extraction = extract_intent_and_entities(message)
    msg_lower = message.lower().strip()
    logger.info(f"Extracted: intent={extraction.intent}, feedback={extraction.feedback_type}, prod={extraction.product_name}")

    # =========================================================================
    # SPECIAL HANDLER: CASE D - TICKET STATUS QUERY (Read-only)
    # =========================================================================
    if re.search(r"\b(status|progress|update)\b", msg_lower) and re.search(r"\bticket\b", msg_lower):
        active_tickets = retrieve_active_tickets(email)
        if not active_tickets:
            return ChatResponse(
                reply=f"Hello {customer_name}. You currently have no active support tickets on your account.",
                ticket_id=None,
                ticket_status=None,
                action_taken="TICKET_STATUS_INQUIRY_EMPTY",
                memory_updated=False,
                retrieved_context=None,
                executed_cypher_summary="GET_ACTIVE_TICKETS -> Returned 0 active tickets (Read-only)"
            )
        ticket = active_tickets[0]
        reply_text = (
            f"Hello {customer_name}. Your Ticket #{ticket.ticket_id} regarding {ticket.product_name} "
            f"is currently {ticket.ticket_status}. Latest troubleshooting step: '{ticket.last_instructions}' "
            f"(Outcome: {ticket.last_outcome_status})."
        )
        return ChatResponse(
            reply=reply_text,
            ticket_id=ticket.ticket_id,
            ticket_status=ticket.ticket_status,
            action_taken="TICKET_STATUS_INQUIRY",
            memory_updated=False,
            retrieved_context=ticket,
            executed_cypher_summary="GET_ACTIVE_TICKETS -> Read-only status inquiry (Zero state mutation)"
        )

    # =========================================================================
    # SPECIAL HANDLER: CASE E - AMBIGUOUS FOLLOW-UP ("I have another problem.")
    # =========================================================================
    is_ambiguous_phrase = bool(
        re.search(r"\b(another\s+(problem|issue)|different\s+(problem|issue)|new\s+problem)\b", msg_lower) and
        not extraction.product_name
    )
    if is_ambiguous_phrase:
        active_tickets = retrieve_active_tickets(email)
        if active_tickets:
            ticket = active_tickets[0]
            return ChatResponse(
                reply=f"Are you experiencing another issue with your {ticket.product_name}, or is this regarding a different product?",
                ticket_id=ticket.ticket_id,
                ticket_status=ticket.ticket_status,
                action_taken="AMBIGUOUS_FOLLOWUP_CLARIFICATION",
                memory_updated=False,
                retrieved_context=ticket,
                executed_cypher_summary="Ambiguous query: Clarification requested (Zero database mutation)"
            )
        else:
            return ChatResponse(
                reply="Could you please specify which product or workspace you are experiencing an issue with?",
                action_taken="AMBIGUOUS_FOLLOWUP_CLARIFICATION",
                memory_updated=False,
                retrieved_context=None,
                executed_cypher_summary="Ambiguous query: Clarification requested (Zero database mutation)"
            )

    # =========================================================================
    # ROUTE A: GENERAL_QUERY
    # =========================================================================
    if extraction.intent == "GENERAL_QUERY":
        dynamic_reply = generate_dynamic_reply(
            prompt=f"Customer '{customer_name}' asked: '{message}'. Provide a helpful, concise answer as an enterprise IT support assistant for Neo4j and related cloud workspaces. Remind them they can report any technical issues or open a ticket anytime.",
            system_prompt="You are an enterprise IT support assistant for Neo4j AuraDB, Graph Data Science Workspaces, and application drivers. Keep answers direct, professional, and under 3 sentences."
        )
        reply_text = dynamic_reply or (
            f"Hello {customer_name}. Our enterprise support team is available 24/7. "
            f"If you are experiencing a technical issue with your workspaces or drivers, please let me know and I will assist you or open a ticket."
        )
        return ChatResponse(
            reply=reply_text,
            ticket_id=None,
            ticket_status=None,
            action_taken="GENERAL_QUERY_RESPONSE",
            memory_updated=False,
            retrieved_context=None,
            executed_cypher_summary="Read-only query: Zero database mutation"
        )

    # =========================================================================
    # ROUTE B: REPORT_NEW_ISSUE (Cases B & C & General Issue Logging)
    # =========================================================================
    if extraction.intent == "REPORT_NEW_ISSUE":
        resolved = resolve_product(extraction.product_name)
        if not resolved:
            return ChatResponse(
                reply="Could you please specify which product or workspace you are experiencing an issue with (e.g. Graph Data Science Workspace, Neo4j AuraDB Enterprise, Python Application Driver)?",
                action_taken="PRODUCT_CLARIFICATION_REQUESTED",
                memory_updated=False,
                retrieved_context=None,
                executed_cypher_summary="Product unmapped: Zero database mutation"
            )

        prod_id, prod_name, prod_category = resolved

        # Check for active ticket on THIS specific product (Idempotency Guard)
        existing_tickets = run_query(cypher.GET_ACTIVE_TICKET_FOR_PRODUCT, {
            "email": email,
            "productId": prod_id
        })
        if existing_tickets:
            et = existing_tickets[0]
            existing_ctx = ActiveTicketContext(
                ticket_id=et.get("ticketId") or "",
                ticket_status=et.get("ticketStatus") or "OPEN",
                product_id=prod_id,
                product_name=prod_name,
                error_code=et.get("errorCode") or "403",
                issue_description=et.get("issueDescription") or "",
                resolution_id=et.get("resolutionId"),
                last_action_name=et.get("lastActionName"),
                last_instructions=et.get("lastInstructions"),
                outcome_id=et.get("outcomeId"),
                last_outcome_status=et.get("lastOutcomeStatus"),
                ticket_updated_at=str(et.get("ticketUpdatedAt")) if et.get("ticketUpdatedAt") else None
            )
            return ChatResponse(
                reply=f"Hello {customer_name}. Ticket #{existing_ctx.ticket_id} is already open for your {prod_name} regarding Error {existing_ctx.error_code}. The current recommended action is: {existing_ctx.last_instructions}",
                ticket_id=existing_ctx.ticket_id,
                ticket_status=existing_ctx.ticket_status,
                action_taken="TICKET_ALREADY_ACTIVE",
                memory_updated=False,
                retrieved_context=existing_ctx,
                executed_cypher_summary=f"MATCH ActiveTicket ({existing_ctx.ticket_id}) -> Ticket already exists (Idempotent bypass)"
            )

        # Ensure product catalog node exists in Neo4j (Do NOT automatically create customer PURCHASED entitlement)
        run_query(cypher.ENSURE_PRODUCT_CATALOG_NODE, {
            "productId": prod_id,
            "productName": prod_name,
            "category": prod_category
        })

        # Calculate ticket sequence number
        count_res = run_query(cypher.GET_TICKET_COUNT_FOR_CUSTOMER, {"email": email})
        existing_count = count_res[0].get("ticketCount", 0) if count_res else 0
        ticket_seq = 101 + existing_count
        ticket_id = f"TK-{ticket_seq}"

        error_code = extraction.error_code or ("403" if "gds" in prod_id.lower() else "ERR-CONFIG")
        issue_id = f"ISS-{ticket_id}-{error_code}"
        resolution_id = f"RES-{ticket_id}-01"
        outcome_id = f"OUT-{ticket_id}-01"
        interaction_id = f"INT-{uuid.uuid4().hex[:8]}"

        diag = DEFAULT_DIAGNOSTICS.get(prod_id, {
            "actionName": "STANDARD_DIAGNOSTIC_RESET",
            "instructions": "Restart client session and verify API credentials."
        })
        action_name = diag["actionName"]
        instructions = diag["instructions"]

        reply_text = (
            f"Hello {customer_name}. I have logged Ticket #{ticket_id} regarding Error {error_code} on your {prod_name}. "
            f"As a Tier-1 troubleshooting step, please {instructions[0].lower() + instructions[1:]} Let me know if the issue persists."
        )

        params = {
            "email": email,
            "productId": prod_id,
            "ticketId": ticket_id,
            "issueId": issue_id,
            "errorCode": error_code,
            "description": extraction.symptom or f"Operational error {error_code} reported on launch",
            "resolutionId": resolution_id,
            "actionName": action_name,
            "instructions": instructions,
            "outcomeId": outcome_id,
            "interactionId": interaction_id,
            "userQuery": message,
            "agentReply": reply_text
        }

        run_query(cypher.CREATE_INITIAL_TICKET, params)

        context = ActiveTicketContext(
            ticket_id=ticket_id,
            ticket_status="OPEN",
            product_id=prod_id,
            product_name=prod_name,
            error_code=error_code,
            issue_description=extraction.symptom or f"Operational error {error_code} reported on launch",
            resolution_id=resolution_id,
            last_action_name=action_name,
            last_instructions=instructions,
            outcome_id=outcome_id,
            last_outcome_status="PENDING"
        )

        return ChatResponse(
            reply=reply_text,
            ticket_id=ticket_id,
            ticket_status="OPEN",
            action_taken="TICKET_CREATED_TIER_1_PRESCRIBED",
            memory_updated=True,
            retrieved_context=context,
            executed_cypher_summary=f"CREATE (t:SupportTicket {{id: '{ticket_id}'}})-[:ATTEMPTED]->(r:Resolution)-[:HAS_OUTCOME]->(o:Outcome {{status: 'PENDING'}})"
        )

    # =========================================================================
    # ROUTE C: ISSUE_FOLLOWUP (Cases A, B, Reassurance, Resolution)
    # =========================================================================
    active_tickets = retrieve_active_tickets(email)

    if len(active_tickets) == 0:
        return ChatResponse(
            reply=f"Hello {customer_name}, I checked your account and found no active support tickets. If you are experiencing a technical issue, please describe what's happening so I can create a new ticket for you.",
            ticket_id=None,
            ticket_status=None,
            action_taken="NO_ACTIVE_TICKETS_FOUND",
            memory_updated=False,
            retrieved_context=None,
            executed_cypher_summary="GET_ACTIVE_TICKETS -> Returned 0 rows"
        )

    # If product specified in follow-up, match specifically to that product's ticket
    selected_ticket = None
    if extraction.product_name:
        resolved = resolve_product(extraction.product_name)
        if resolved:
            target_prod_id = resolved[0]
            for t in active_tickets:
                if t.product_id == target_prod_id:
                    selected_ticket = t
                    break

    if not selected_ticket:
        if len(active_tickets) >= 2:
            ticket_summaries = ", ".join([f"#{t.ticket_id} ({t.product_name})" for t in active_tickets])
            return ChatResponse(
                reply=f"I noticed multiple open tickets on your account: {ticket_summaries}. Which specific issue are you following up on?",
                ticket_id=None,
                ticket_status=None,
                action_taken="DISAMBIGUATION_PROMPT",
                memory_updated=False,
                retrieved_context=None,
                executed_cypher_summary="GET_ACTIVE_TICKETS -> Multiple rows detected, requesting disambiguation"
            )
        selected_ticket = active_tickets[0]

    ticket = selected_ticket

    # Sub-case C1: Explicit Persistent Failure ("It's still not working", Case A & Case B)
    if extraction.feedback_type == "PERSISTENT_FAILURE":
        # Check if already escalated (Session 2 Idempotency Guard)
        if ticket.ticket_status == "ESCALATED":
            reply_text = (
                f"Welcome back {customer_name}. Ticket #{ticket.ticket_id} regarding your {ticket.product_name} "
                f"is already escalated and queued for Tier-2 engineering review. A senior cloud engineer is actively "
                f"verifying your license provisioning."
            )
            return ChatResponse(
                reply=reply_text,
                ticket_id=ticket.ticket_id,
                ticket_status="ESCALATED",
                action_taken="ALREADY_ESCALATED_REASSURANCE",
                memory_updated=False,
                retrieved_context=ticket,
                executed_cypher_summary="Ticket already ESCALATED: No duplicate resolution created (Idempotent bypass)"
            )

        new_res_id = f"RES-{ticket.ticket_id}-02"
        new_out_id = f"OUT-{ticket.ticket_id}-02"
        interaction_id = f"INT-{uuid.uuid4().hex[:8]}"
        new_action = "TIER_2_ESCALATION"
        new_instructions = "Automated diagnostic snapshot forwarded for license reprovisioning."

        reply_text = (
            f"Welcome back {customer_name}. I see that {ticket.last_action_name or 'the previous step'} did not "
            f"resolve Error {ticket.error_code} on your {ticket.product_name}. Since Tier-1 troubleshooting failed, "
            f"I have escalated Ticket #{ticket.ticket_id} in the support workflow for Tier-2 review."
        )

        params = {
            "ticketId": ticket.ticket_id,
            "outcomeId": ticket.outcome_id,
            "feedback": message,
            "newResolutionId": new_res_id,
            "newActionName": new_action,
            "newInstructions": new_instructions,
            "newOutcomeId": new_out_id,
            "interactionId": interaction_id,
            "userQuery": message,
            "agentReply": reply_text
        }

        run_query(cypher.MUTATE_TICKET_ESCALATE, params)

        ticket.ticket_status = "ESCALATED"
        ticket.last_action_name = new_action
        ticket.last_instructions = new_instructions
        ticket.last_outcome_status = "PENDING"

        return ChatResponse(
            reply=reply_text,
            ticket_id=ticket.ticket_id,
            ticket_status="ESCALATED",
            action_taken="RESOLUTION_FAILED_TICKET_ESCALATED",
            memory_updated=True,
            retrieved_context=ticket,
            executed_cypher_summary=f"SET Outcome({ticket.outcome_id}).status = 'FAILED', Ticket({ticket.ticket_id}).status = 'ESCALATED', CREATE (r2:Resolution {{actionName: 'TIER_2_ESCALATION'}})"
        )

    # Sub-case C2: Resolved Confirmation
    elif extraction.feedback_type == "RESOLVED":
        interaction_id = f"INT-{uuid.uuid4().hex[:8]}"
        reply_text = f"Wonderful news, {customer_name}! I have updated Ticket #{ticket.ticket_id} as RESOLVED. Please reach out if you need anything else."
        params = {
            "ticketId": ticket.ticket_id,
            "outcomeId": ticket.outcome_id,
            "feedback": message,
            "interactionId": interaction_id,
            "userQuery": message,
            "agentReply": reply_text
        }
        run_query(cypher.MUTATE_TICKET_RESOLVE, params)

        ticket.ticket_status = "RESOLVED"
        ticket.last_outcome_status = "SUCCESS"

        return ChatResponse(
            reply=reply_text,
            ticket_id=ticket.ticket_id,
            ticket_status="RESOLVED",
            action_taken="TICKET_RESOLVED_SUCCESSFULLY",
            memory_updated=True,
            retrieved_context=ticket,
            executed_cypher_summary=f"SET Outcome({ticket.outcome_id}).status = 'SUCCESS', Ticket({ticket.ticket_id}).status = 'RESOLVED'"
        )

    # Sub-case C3: Neutral / Question during ongoing ticket
    else:
        reply_text = (
            f"Hello {customer_name}, I am tracking your active Ticket #{ticket.ticket_id} regarding {ticket.product_name}. "
            f"The recommended action was: '{ticket.last_instructions}'. Please let me know if this step resolved the issue or if the error persists."
        )
        return ChatResponse(
            reply=reply_text,
            ticket_id=ticket.ticket_id,
            ticket_status=ticket.ticket_status,
            action_taken="ACTIVE_TICKET_CLARIFICATION",
            memory_updated=False,
            retrieved_context=ticket,
            executed_cypher_summary="GET_ACTIVE_TICKETS -> Retrieved context without state mutation"
        )
