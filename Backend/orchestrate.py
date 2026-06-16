import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.tools import tool
from rapidfuzz import fuzz
import custom_Agent

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file")

MODEL = ChatGroq(
    api_key=API_KEY,
    model="llama-3.3-70b-versatile"
)


# ==========================================
# Tools
# ==========================================

@tool
def finance_assistant(query: str) -> str:
    """Retrieve finance related information."""
    return custom_Agent.get_finance_datas(query)

@tool
def information_technology_assistant(query: str) -> str:
    """Retrieve IT related information."""
    return custom_Agent.get_IT_datas(query)

@tool
def company_assistant(query: str) -> str:
    """Retrieve company related information."""
    return custom_Agent.get_company_datas(query)

@tool
def hr_assistant(query: str) -> str:
    """Retrieve HR related information."""
    return custom_Agent.get_hr_datas(query)

@tool
def general_assistant(query: str) -> str:
    """Retrieve general facilities information."""
    return custom_Agent.get_general_datas(query)


# ==========================================
# Keyword Lists
# ==========================================

FINANCE_KEYWORDS = [
    "salary", "payroll", "bonus", "allowance", "reimbursement",
    "tax", "finance", "credited", "credit",
    "salary policy", "salary revision", "salary increase", "pay date",
    "payment", "paid", "payroll date", "salary credit",
    "form 16", "tds", "investment declaration", "travel claim",
    "expense claim", "expense", "submit expense", "claim expense",
    "petty cash", "advance", "loan","salary credited","payroll",
    "insurance claim", "medical claim", "dental", "optical",
    "reimbursement limit", "per diem", "travel policy",
    "cutoff","payroll cut", "variable pay", "salary structure",
]

IT_KEYWORDS = [
    "vpn", "password", "password reset", "forgot password", "software",
    "software installation", "laptop", "desktop", "printer", "network",
    "wifi", "wi-fi", "outlook", "teams", "sharepoint", "onedrive",
    "security", "mfa", "technical issue", "login issue",
    "account locked", "helpdesk", "it support", "blue screen",
    "slow laptop", "not working", "not responding", "software crash",
    "virus", "antivirus", "backup", "data recovery", "access denied",
    "email", "mailbox", "calendar", "meeting link", "zoom",
]

COMPANY_KEYWORDS = [
    "hexaware", "company", "ceo", "founder", "headquarters",
    "mission", "vision", "leadership", "services", "located",
    "location",  "employees", "history",
    "about hexaware", "hexaware revenue", "hexaware offices",
    "hexaware clients", "hexaware industries", "hexaware career",
    "hexaware culture", "hexaware values", "hexaware awards",
    "what does hexaware", "tell me about hexaware",
    "chairman","executive director","leadership team",
]

HR_KEYWORDS = [
    "leave", "leave policy", "casual leave", "sick leave", "annual leave",
    "leave days", "leave balance", "leave application", "leave request",
    "wfh", "wff", "wfh policy", "apply wfh", "work from home",
    "remote work", "remote", "hybrid", "work remotely",
    "holiday", "public holiday", "working hours", "office hours",
    "probation", "confirmation", "notice period", "resignation",
    "insurance", "medical", "health", "employee benefits", "hr",
    "appraisal", "performance review", "rating", "increment",
    "maternity", "paternity", "bereavement", "marriage leave",
    "attendance", "late", "biometric", "overtime", "comp off",
    "posh", "grievance", "complaint", "harassment",
    "training", "certification", "learning", "course",
    "payslip", "salary slip", "pf", "gratuity", "uan",
    "exit", "full and final", "relieving letter", "experience letter",
]

GENERAL_KEYWORDS = [
    "cafeteria", "canteen", "food", "lunch", "breakfast", "dinner",
    "meal", "snack", "eating",
    "transport", "bus", "shuttle", "cab", "taxi", "commute",
    "pickup", "drop", "vehicle",
    "parking", "park", "car park", "two wheeler", "bike",
    "meeting room", "conference room", "book room", "room booking",
    "auditorium", "town hall", "training room",
    "id card", "access card", "badge", "entry card", "visitor",
    "gym", "fitness", "workout", "exercise", "yoga", "wellness",
    "fire", "emergency", "evacuation", "safety", "first aid",
    "stationery", "office supply", "pen", "notebook", "printer paper",
    "dress code", "attire", "formal", "casual friday",
    "ac", "air conditioning", "temperature", "housekeeping",
    "workstation", "desk", "seating", "chair", "ergonomic",
    "event", "celebration", "birthday", "anniversary", "team outing",
    "locker", "smoking", "drinking water", "washroom", "toilet",
    "lift", "elevator", "security",
]

# Order matters — Finance and HR before General
DOMAIN_MAP = {
    "finance": FINANCE_KEYWORDS,
    "hr":      HR_KEYWORDS,
    "it":      IT_KEYWORDS,
    "company": COMPANY_KEYWORDS,
    "general": GENERAL_KEYWORDS,
}

RETRIEVER_MAP = {
    "finance": custom_Agent.get_finance_datas,
    "it":      custom_Agent.get_IT_datas,
    "company": custom_Agent.get_company_datas,
    "hr":      custom_Agent.get_hr_datas,
    "general": custom_Agent.get_general_datas,
}

NO_RESULT_MARKERS = [
    "No finance information found",
    "No IT information found",
    "No company information found",
    "No HR information found",
    "No facilities information found",
]

IDENTITY_QUERIES = [
    "who are you", "tell me about yourself",
    "what are you", "what can you do",
    "who made you", "are you a bot", "are you an ai",
]


# ==========================================
# Related Questions
# ==========================================

RELATED_QUESTIONS = {
    "hr": {
        "leave": [
            "Can I carry forward my unused leaves?",
            "How do I apply for leave on the HR portal?",
            "What is the sick leave policy?",
        ],
        "wfh": [
            "How many WFH days am I allowed per week?",
            "What are the office working hours?",
            "Do I need manager approval for WFH?",
        ],
        "salary": [
            "How do I download my payslip?",
            "When is the annual increment effective?",
            "How do I submit my tax investment declaration?",
        ],
        "insurance": [
            "How do I file a medical reimbursement claim?",
            "Are my parents covered under health insurance?",
            "Where can I find the list of network hospitals?",
        ],
        "appraisal": [
            "What is the performance rating scale?",
            "When are appraisal results announced?",
            "How is the performance bonus calculated?",
        ],
        "resignation": [
            "What is the notice period after confirmation?",
            "When will I receive my relieving letter?",
            "When is full and final settlement processed?",
        ],
        "default": [
            "How many leave days do I have?",
            "How do I apply for WFH?",
            "What is the notice period?",
        ],
    },
    "finance": {
        "salary": [
            "How do I download my payslip?",
            "What are the salary components?",
            "How do I report a salary discrepancy?",
        ],
        "reimbursement": [
            "What expenses are not reimbursable?",
            "How long does reimbursement take?",
            "What is the travel expense limit?",
        ],
        "tax": [
            "When is Form 16 issued?",
            "What investment proofs are accepted?",
            "How do I activate my PF UAN?",
        ],
        "bonus": [
            "When is the performance bonus paid?",
            "What is the salary increment range?",
            "Am I eligible for the referral bonus?",
        ],
        "default": [
            "When is salary credited?",
            "How do I submit an expense claim?",
            "How do I get my Form 16?",
        ],
    },
    "it": {
        "vpn": [
            "What is the VPN server address?",
            "How do I set up MFA on my phone?",
            "What should I do if VPN keeps disconnecting?",
        ],
        "password": [
            "How often do I need to change my password?",
            "What are the password requirements?",
            "How do I set up Microsoft Authenticator?",
        ],
        "laptop": [
            "How do I raise a hardware repair ticket?",
            "Can I get a loaner laptop while mine is repaired?",
            "What is the laptop repair SLA?",
        ],
        "software": [
            "What software can I install myself?",
            "How do I request new software installation?",
            "What software comes pre-installed on my laptop?",
        ],
        "default": [
            "How do I connect to the office Wi-Fi?",
            "How do I reset my password?",
            "How do I raise an IT support ticket?",
        ],
    },
    "company": {
        "default": [
            "What services does Hexaware offer?",
            "How many employees does Hexaware have?",
            "What industries does Hexaware serve?",
        ],
    },
    "general": {
        "cafeteria": [
            "What are the cafeteria timings?",
            "Is the cafeteria subsidized?",
            "Can I order food delivery to the office?",
        ],
        "transport": [
            "How do I register for company transport?",
            "How do I request a late-night cab?",
            "What are the shuttle timings?",
        ],
        "meeting room": [
            "How do I book a meeting room?",
            "What facilities are available in meeting rooms?",
            "How do I request catering for a meeting?",
        ],
        "default": [
            "How do I book a meeting room?",
            "How do I register for company transport?",
            "How do I get a replacement ID card?",
        ],
    },
}


def get_related_questions(domain: str, question: str) -> str:
    if domain not in RELATED_QUESTIONS:
        return ""

    domain_map = RELATED_QUESTIONS[domain]
    question_lower = question.lower()

    all_suggestions = []
    matched_topic_suggestions = []

    for topic, questions in domain_map.items():
        if topic == "default":
            continue
        if topic in question_lower:
            matched_topic_suggestions = questions
        else:
            all_suggestions.extend(questions)

    default_suggestions = domain_map.get("default", [])

    final_suggestions = []
    for q in all_suggestions:
        if q not in final_suggestions and q.lower() not in question_lower:
            final_suggestions.append(q)
        if len(final_suggestions) >= 3:
            break

    if len(final_suggestions) < 3:
        for q in matched_topic_suggestions + default_suggestions:
            if q not in final_suggestions and q.lower() not in question_lower:
                final_suggestions.append(q)
            if len(final_suggestions) >= 3:
                break

    if not final_suggestions:
        return ""

    lines = "\n".join(f"• {q}" for q in final_suggestions[:3])
    return f"\n\n💡 **You might also want to ask:**\n{lines}"


# ==========================================
# Domain Detector
# ==========================================

BLOCKLIST = {
    "ho", "hoo", "hooo", "hoooo",
    "he", "she", "hi", "hey", "ha",
    "ok", "okay", "k", "yes", "no",
    "hmm", "hm", "ah", "oh", "uh",
    "lol", "haha", "hehe",
}


def detect_domain(text: str) -> str | None:
    text_lower = text.lower().strip()
    text_lower = text_lower.replace("?", "").replace("!", "").replace(",", "").replace(".", "")
    text_lower = " ".join(text_lower.split())

    if text_lower in BLOCKLIST:
        return None

    words = text_lower.split()
    if len(words) == 1 and len(text_lower) <= 3:
        for domain, keywords in DOMAIN_MAP.items():
            if text_lower in keywords:
                return domain
        return None

    # Step 1 — exact match
    for domain, keywords in DOMAIN_MAP.items():
        if any(kw in text_lower for kw in keywords):
            return domain

    # Step 2 — fuzzy match
    words = text_lower.split()
    for domain, keywords in DOMAIN_MAP.items():
        for kw in keywords:
            kw_words = kw.split()
            if len(kw_words) == 1:
                for word in words:
                    if len(word) >= 3:
                        if len(kw.split()) > 1:
                            continue
                        threshold = 72 if len(word) <= 4 else 80
                        if fuzz.ratio(word, kw) >= threshold:
                            print(f"Fuzzy match: '{word}' → '{kw}' ({domain})")
                            return domain
            else:
                if len(text_lower.strip()) >= 5 and fuzz.partial_ratio(kw, text_lower) >= 82:
                    print(f"Fuzzy match: '{text_lower}' → '{kw}' ({domain})")
                    return domain

    return None


# ==========================================
# Query Expander
# ==========================================
# FIX Bug 1 & 2: expand_query is now defined/imported here so route_query
# can call it before domain detection and before retrieval.
# If your expand_query lives in Backend_server.py, replace this function
# body with:  from Backend_server import expand_query

def expand_query(query: str) -> str:
    """
    Expand short or ambiguous queries into a richer sentence so that
    domain detection and vector retrieval work on meaningful text.

    Examples
    --------
    "hexaware"  →  "Tell me about Hexaware company, its history and services"
    "wfh"       →  "What is the work from home policy at Hexaware?"
    "payslip"   →  "How do I download my payslip or salary slip?"
    """
    # Short-form / acronym expansions
    EXPANSIONS = {
        "wfh":      "What is the work from home policy at Hexaware?",
        "wff":      "What is the work from facility policy at Hexaware?",
        "pf":       "Tell me about provident fund PF policy at Hexaware",
        "uan":      "How do I activate or find my UAN provident fund number?",
        "tds":      "Tell me about TDS tax deduction at source for salary",
        "mfa":      "How do I set up multi-factor authentication MFA?",
        "vpn":      "How do I connect to or set up the VPN?",
        "hr":       "What are the HR human resources policies at Hexaware?",
        "it":       "How do I contact IT support at Hexaware?",
        "hexaware": "Tell me about Hexaware company, its history, services, and leadership",
        "payslip":  "How do I download my payslip or salary slip?",
        "appraisal":"What is the performance appraisal process at Hexaware?",
        "increment":"What is the salary increment or raise policy at Hexaware?",
        "gratuity": "How is gratuity calculated and paid at Hexaware?",
        "posh":     "What is the POSH policy on prevention of sexual harassment?",
    }

    stripped = query.strip().lower()

    # Direct acronym / keyword expansion
    if stripped in EXPANSIONS:
        return EXPANSIONS[stripped]

    # Query is already long enough — return as-is
    if len(stripped.split()) >= 5:
        return query

    # Partial expansions: inject known terms into the query for better recall
    for key, expansion in EXPANSIONS.items():
        if stripped == key or stripped.startswith(key + " ") or stripped.endswith(" " + key):
            return f"{query} — {expansion}"

    return query


# ==========================================
# Context Parser
# ==========================================

def parse_context_query(full_input: str) -> tuple[str, str]:
    marker = "Current User Question:"
    if marker in full_input:
        parts = full_input.split(marker, 1)
        history = parts[0].replace("Previous Conversation:", "").strip()
        question = parts[1].strip()
        return history, question
    return "", full_input.strip()


# ==========================================
# Route Query  (Bugs 1, 2, 3 fixed here)
# ==========================================

def route_query(full_input: str) -> tuple[str | None, str]:
    history, question = parse_context_query(full_input)

    # ── FIX Bug 1 & 2 ──────────────────────────────────────────────────────
    # Always expand the question before domain detection AND retrieval.
    # Previously, expand_query() result was used only in Backend_server.py
    # and never passed here, so detection ran on the raw (often too short)
    # question and the retriever also got the unexpanded query.
    expanded_question = expand_query(question)
    # ───────────────────────────────────────────────────────────────────────

    domain = detect_domain(expanded_question)   # FIX: was detect_domain(question)

    FOLLOW_UP_SIGNALS = [
        "it ", "he ", "she ", "they ", "that ", "this ", "those ",
        "tell me more", "explain more", "what about", "more details",
        "and what", "also ", "additionally"
    ]
    is_follow_up = any(
        expanded_question.lower().strip().startswith(s)
        for s in FOLLOW_UP_SIGNALS
    )

    if domain is None and is_follow_up and history:
        # FIX Bug 2: expand history as well before detecting domain
        domain = detect_domain(expand_query(history))

    if domain is None:
        return None, "unknown"

    # ── FIX Bug 1 ──────────────────────────────────────────────────────────
    # Use expanded_question as the retrieval query so vector search gets
    # richer, more specific text to match against.
    if is_follow_up and history:
        retrieval_query = (
            f"Context from previous conversation: {history}\n"
            f"Current question: {expanded_question}"
        )
    else:
        retrieval_query = expanded_question   # FIX: was `question` (or full_input)
    # ───────────────────────────────────────────────────────────────────────

    print(f"\n========== {domain.upper()} ROUTE ==========")
    print(f"Original question : {question}")
    print(f"Expanded question : {expanded_question}")
    print(f"Retrieval query   :\n{retrieval_query}\n")

    retriever = RETRIEVER_MAP[domain]
    context = retriever(retrieval_query)

    return context, domain


# ==========================================
# Agent Executor  (Bug 4 fixed here)
# ==========================================

class SimpleAgentExecutor:

    def invoke(self, data: dict) -> dict:

        full_input = data["input"]
        _, question = parse_context_query(full_input)

        if question.lower().strip() in IDENTITY_QUERIES:
            return {
                "output": (
                    "I am Hexaware AI Assistant. I can help you with "
                    "HR policies, IT support, Finance queries, company "
                    "information, and general facilities."
                )
            }

        print("\n===================")
        print("FULL INPUT RECEIVED")
        print(full_input)
        print("===================\n")

        context, domain = route_query(full_input)

        if context is None:
            return {
                "output": (
                    "I couldn't find relevant information for your query. "
                    "You can ask me about HR policies, IT support, Finance, "
                    "company information, or general facilities."
                )
            }

        if any(marker in context for marker in NO_RESULT_MARKERS):
            return {
                "output": (
                    f"I couldn't find specific information about that in the "
                    f"{domain.upper()} knowledge base. "
                    f"Please contact the relevant team directly."
                )
            }

        _, question = parse_context_query(full_input)

        # ── FIX Bug 4 ───────────────────────────────────────────────────────
        # Removed the hard "1-3 sentences" cap that was cutting off real
        # answers (e.g. multi-step reimbursement procedures, resignation
        # checklists). The model is now free to be as concise or as detailed
        # as the context demands.
        prompt = f"""Context:
{context}

Based ONLY on the context above, answer the following question clearly and completely.
Be concise but include all relevant details the employee needs to act on this.
Do not include information that is not present in the context above.

Question: {question}"""
        # ────────────────────────────────────────────────────────────────────

        response = MODEL.invoke(prompt)

        related = get_related_questions(domain, question)

        return {"output": response.content + related}


agent_executor = SimpleAgentExecutor()


# ==========================================
# CLI Test
# ==========================================

if __name__ == "__main__":

    session_history = []
    print("Hexaware AI Assistant — type 'exit' to quit\n")

    while True:
        query = input("Ask Question: ").strip()

        if query.lower() == "exit":
            break
        if not query:
            continue

        follow_up_words = [
            "it", "he", "she", "they", "them", "that", "this",
            "where", "when", "more", "who", "which",
            "tell me more", "explain more", "what about",
        ]

        query_lower = query.lower()
        is_follow_up = any(query_lower.startswith(w) for w in follow_up_words)

        if is_follow_up and session_history:
            full_input = (
                f"Previous Conversation:\n\n{session_history[-3:]}\n\n"
                f"Current User Question:\n\n{query}"
            )
        else:
            full_input = query

        result = agent_executor.invoke({"input": full_input})

        print("\n====================")
        print("ANSWER")
        print("====================")
        print(result["output"])

        session_history.append({"user": query, "assistant": result["output"]})