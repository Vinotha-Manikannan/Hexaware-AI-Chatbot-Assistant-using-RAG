import os
import uuid
import sqlite3
import asyncio
from contextlib import contextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jose import JWTError, jwt
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer
from rapidfuzz import fuzz, process
import Model
import orchestrate
import custom_Agent

# ==========================================
# Load environment variables from .env
# ==========================================

load_dotenv()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")
ADMIN_USERS    = {ADMIN_USERNAME: ADMIN_PASSWORD}

# ==========================================
# JWT config — loaded from .env
# JWT_SECRET must be a long random string
# TOKEN_EXPIRE_HOURS controls how long tokens last
# ==========================================

JWT_SECRET         = os.getenv("JWT_SECRET", "please-change-this-secret")
JWT_ALGORITHM      = "HS256"
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "8"))


def create_access_token(username: str) -> str:
    """
    Creates a signed JWT token.
    Contains: username + expiry time.
    Signed with JWT_SECRET — cannot be forged without it.
    """
    expire  = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    """
    Verifies the JWT signature and expiry.
    Returns username if valid.
    Raises HTTPException if invalid or expired.
    """
    try:
        payload  = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError as e:
        error_msg = str(e)
        if "expired" in error_msg:
            raise HTTPException(status_code=401, detail="Token expired — please log in again")
        raise HTTPException(status_code=401, detail="Invalid token")


from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer

app = FastAPI(
    title="RAG Agent API",
    description="API for RAG-based knowledge base management and chat",
    version="1.0.0"
)

# ==========================================
# Adds the 🔒 Authorize button to Swagger UI
# So you can test protected endpoints easily
# ==========================================

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

KNOWLEDGE_BASE_DIR = Path("KnowledgeBase")
KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)

# ==========================================
# SQLite — tickets + pending_tickets
# ==========================================

DB_PATH = Path("tickets.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id     TEXT PRIMARY KEY,
                issue         TEXT NOT NULL,
                category      TEXT NOT NULL DEFAULT 'IT',
                status        TEXT NOT NULL DEFAULT 'Open',
                priority      TEXT NOT NULL DEFAULT 'Low',
                employee_name TEXT,
                employee_id   TEXT,
                department    TEXT,
                session_id    TEXT,
                created_at    TEXT NOT NULL,
                updated_at    TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_tickets (
                session_id  TEXT PRIMARY KEY,
                issue       TEXT NOT NULL,
                category    TEXT NOT NULL DEFAULT 'IT',
                stage       TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)
        conn.commit()


init_db()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


# ==========================================
# Ticket DB helpers
# ==========================================

def db_get_all_tickets() -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM tickets ORDER BY created_at DESC"
        ).fetchall()
    return [row_to_dict(r) for r in rows]


def db_get_ticket(ticket_id: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)
        ).fetchone()
    return row_to_dict(row) if row else None


def db_insert_ticket(ticket: dict):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO tickets
              (ticket_id, issue, category, status, priority,
               employee_name, employee_id, department, session_id,
               created_at, updated_at)
            VALUES
              (:ticket_id, :issue, :category, :status, :priority,
               :employee_name, :employee_id, :department, :session_id,
               :created_at, :updated_at)
        """, ticket)
        conn.commit()


def db_update_ticket(ticket_id: str, status: str, priority: Optional[str], updated_at: str):
    with get_db() as conn:
        if priority:
            conn.execute(
                "UPDATE tickets SET status=?, priority=?, updated_at=? WHERE ticket_id=?",
                (status, priority, updated_at, ticket_id),
            )
        else:
            conn.execute(
                "UPDATE tickets SET status=?, updated_at=? WHERE ticket_id=?",
                (status, updated_at, ticket_id),
            )
        conn.commit()


def db_delete_ticket(ticket_id: str):
    with get_db() as conn:
        conn.execute("DELETE FROM tickets WHERE ticket_id=?", (ticket_id,))
        conn.commit()


# ==========================================
# Pending ticket DB helpers
# ==========================================

def db_get_pending(session_id: str) -> Optional[dict]:
    """
    Returns pending ticket for session — but auto-expires
    any pending ticket older than 30 minutes.
    This prevents stale ticket flows from blocking new chats.
    """
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM pending_tickets WHERE session_id = ?", (session_id,)
        ).fetchone()

    if not row:
        return None

    pending = row_to_dict(row)

    # Auto-expire if older than 30 minutes
    try:
        updated_at = datetime.strptime(pending["updated_at"], "%Y-%m-%d %H:%M:%S")
        age_minutes = (datetime.now() - updated_at).total_seconds() / 60
        if age_minutes > 30:
            db_delete_pending(session_id)
            print(f"Auto-expired pending ticket for session {session_id} (age: {age_minutes:.1f} min)")
            return None
    except Exception:
        pass

    return pending


def db_set_pending(session_id: str, issue: str, category: str, stage: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute("""
            INSERT INTO pending_tickets (session_id, issue, category, stage, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                issue      = excluded.issue,
                category   = excluded.category,
                stage      = excluded.stage,
                updated_at = excluded.updated_at
        """, (session_id, issue, category, stage, now))
        conn.commit()


def db_delete_pending(session_id: str):
    with get_db() as conn:
        conn.execute("DELETE FROM pending_tickets WHERE session_id=?", (session_id,))
        conn.commit()


# ==========================================
# In-memory chat history
# ==========================================

chat_sessions: dict = {}


# ==========================================
# Models
# ==========================================

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    chat_history: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    response: str
    status: str = "success"


class FileUploadResponse(BaseModel):
    filename: str
    size: int
    collection_name: str
    status: str
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    message: str
    status: str = "success"
    expires_in: str = f"{TOKEN_EXPIRE_HOURS} hours"


class TicketStatusUpdate(BaseModel):
    status: str
    priority: Optional[str] = None


# ==========================================
# Auth — now uses JWT verify
# ==========================================

def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized - No token provided")
    token = authorization.replace("Bearer ", "")
    # decode_access_token raises HTTPException if invalid/expired
    decode_access_token(token)
    return True


# ==========================================
# Health
# ==========================================

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "RAG Agent API is running",
        "version": "1.0.0"
    }


# ==========================================
# Login — returns signed JWT now
# ==========================================

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    try:
        if ADMIN_USERS.get(credentials.username) == credentials.password:
            token = create_access_token(credentials.username)
            return LoginResponse(
                token=token,
                message="Login successful",
                status="success",
                expires_in=f"{TOKEN_EXPIRE_HOURS} hours"
            )
        raise HTTPException(status_code=401, detail="Invalid username or password")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Priority Detection
# ==========================================

def detect_priority(issue: str) -> str:
    issue_lower = issue.lower()
    critical_keywords = [
        "server down", "data loss", "breach", "hacked", "ransomware",
        "production down", "system crash", "blue screen", "complete failure",
        "entire network down", "database corrupted"
    ]
    high_keywords = [
        "not working", "urgent", "asap", "overheating", "cannot login",
        "access denied", "account locked", "vpn not connecting",
        "cannot access", "login failed", "permission denied", "critical error"
    ]
    medium_keywords = [
        "slow", "not syncing", "printer", "outlook", "wifi",
        "disconnecting", "not responding", "keeps crashing", "freezing",
        "internet issue", "network issue", "software crash"
    ]
    if any(k in issue_lower for k in critical_keywords):
        return "Critical"
    if any(k in issue_lower for k in high_keywords):
        return "High"
    if any(k in issue_lower for k in medium_keywords):
        return "Medium"
    return "Low"


# ==========================================
# Query Expander — with fuzzy typo tolerance
# ==========================================

EXPANSIONS = {
    "hexaware":            "What is Hexaware Technologies? Tell me about the company.",
    "hexware":             "What is Hexaware Technologies? Tell me about the company.",
    "about hexaware":      "What is Hexaware Technologies? Tell me about the company.",
    "tell about hexaware": "What is Hexaware Technologies? Tell me about the company.",
    "tell about hexware":  "What is Hexaware Technologies? Tell me about the company.",
    "company":             "Tell me about the company and its services.",
    "about company":       "Tell me about the company and its services.",
    "hr":                  "What are the HR policies of the company?",
    "hr policy":           "What are the HR policies of the company?",
    "leave":               "What is the leave policy?",
    "leave policy":        "What is the leave policy?",
    "salary":              "What is the salary structure and pay policy?",
    "appraisal":           "How does the appraisal and performance review process work?",
    "benefits":            "What are the employee benefits?",
    "onboarding":          "What is the onboarding process for new employees?",
    "it":                  "What IT support services are available?",
    "it support":          "What IT support services are available?",
    "vpn":                 "How do I connect to VPN? What are the VPN setup instructions?",
    "wifi":                "How do I connect to the office WiFi network?",
    "laptop":              "What are the laptop usage policies and support options?",
    "finance":             "What are the finance and reimbursement policies?",
    "reimbursement":       "What is the expense reimbursement process?",
    "expenses":            "How do I submit expense claims?",
}

def expand_query(query: str) -> str:
    q = query.lower().strip()

    # Step 1 — exact match only
    if q in EXPANSIONS:
        return EXPANSIONS[q]

    # Step 2 — fuzzy match only for short queries
    if len(q.split()) <= 3:

        result = process.extractOne(
            q,
            EXPANSIONS.keys(),
            scorer=fuzz.ratio,
            score_cutoff=85
        )

        if result:
            return EXPANSIONS[result[0]]

    return query


# ==========================================
# Parse employee details
# ==========================================

def parse_employee_details(text: str) -> Optional[dict]:
    for sep in ["|", ","]:
        parts = [p.strip() for p in text.split(sep)]
        if len(parts) == 3 and all(parts):
            return {
                "employee_name": parts[0],
                "employee_id":   parts[1],
                "department":    parts[2],
            }
    return None


# ==========================================
# File Upload
# ==========================================

@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    domain: str = Form(...),
    auth: bool = Depends(verify_token)
):
    try:
        allowed_extensions = {".pdf", ".txt", ".doc", ".docx", ".csv"}
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type {file_extension} not supported")

        domain_dir = KNOWLEDGE_BASE_DIR / domain
        domain_dir.mkdir(parents=True, exist_ok=True)

        file_path = domain_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = file_path.stat().st_size
        collection_name = f"{domain}_datas"
        custom_Agent.process_data(str(file_path), collection_name)

        return FileUploadResponse(
            filename=file.filename,
            size=file_size,
            collection_name=collection_name,
            status="success",
            message=f"File processed and added to {domain} domain"
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Files
# ==========================================

@app.get("/api/files/{domain}")
async def get_domain_files(domain: str, auth: bool = Depends(verify_token)):
    try:
        domain_dir = KNOWLEDGE_BASE_DIR / domain
        if not domain_dir.exists():
            return {"files": [], "domain": domain, "count": 0, "status": "success"}

        files = []
        for file_path in domain_dir.glob("*.*"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "id": hash(file_path.name),
                    "name": file_path.name,
                    "size": f"{stat.st_size / 1024:.2f} KB",
                    "uploadTime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
        return {"files": files, "domain": domain, "count": len(files), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/files/{domain}/{filename}")
async def delete_file(domain: str, filename: str, auth: bool = Depends(verify_token)):
    try:
        file_path = KNOWLEDGE_BASE_DIR / domain / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        os.remove(file_path)
        return {"status": "success", "message": f"File '{filename}' deleted from {domain} domain"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/{domain}/{filename}/content")
async def get_file_content(domain: str, filename: str, auth: bool = Depends(verify_token)):
    try:
        file_path = KNOWLEDGE_BASE_DIR / domain / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content, "filename": filename, "domain": domain, "status": "success"}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Cannot read file - binary format not supported for viewing")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Domains
# ==========================================

@app.get("/api/domains")
async def get_domains(auth: bool = Depends(verify_token)):
    try:
        domains = []
        for item in KNOWLEDGE_BASE_DIR.iterdir():
            if item.is_dir():
                domains.append({"name": item.name, "fileCount": len(list(item.glob("*.*")))})
        return {"domains": domains, "count": len(domains), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Ticket Endpoints
# ==========================================

@app.get("/api/tickets")
async def get_tickets(auth: bool = Depends(verify_token)):
    try:
        ticket_list = db_get_all_tickets()
        return {"tickets": ticket_list, "count": len(ticket_list), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/tickets/{ticket_id}")
async def update_ticket_status(
    ticket_id: str,
    update: TicketStatusUpdate,
    auth: bool = Depends(verify_token)
):
    if db_get_ticket(ticket_id) is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    allowed_status = ["Open", "In Progress", "Resolved"]
    if update.status not in allowed_status:
        raise HTTPException(status_code=400, detail=f"Status must be one of {allowed_status}")

    allowed_priority = ["Low", "Medium", "High", "Critical"]
    if update.priority and update.priority not in allowed_priority:
        raise HTTPException(status_code=400, detail=f"Priority must be one of {allowed_priority}")

    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_update_ticket(ticket_id, update.status, update.priority, updated_at)
    return {"status": "success", "ticket": db_get_ticket(ticket_id)}


@app.delete("/api/tickets/{ticket_id}")
async def delete_ticket(ticket_id: str, auth: bool = Depends(verify_token)):
    if db_get_ticket(ticket_id) is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    db_delete_ticket(ticket_id)
    return {"status": "success", "message": f"Ticket {ticket_id} deleted"}


# ==========================================
# Chat
# ==========================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Input length guard
        if len(request.message) > 1000:
            raise HTTPException(status_code=400, detail="Message too long (max 1000 characters)")

        session_id   = request.session_id
        refine_query = request.message
        query_lower  = refine_query.lower().strip()

        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        history = chat_sessions[session_id]

        # ==========================================
        # Greetings / Small-talk
        # ==========================================

        # ==========================================
        # Greetings — fuzzy + expanded variations
        # ==========================================

        GREETING_WORDS = {
            "hi", "hii", "hiii", "hiiii", "helo", "hello", "helo",
            "hey", "heya", "heyy", "hlo", "hai", "haii",
            "hi there", "hello there", "hey there",
            "howdy", "sup", "what's up", "whats up", "wassup",
            "good day", "greetings",
        }
        MORNING_WORDS = {
            "good morning", "gm", "good mrng", "gud morning",
            "good moring", "goood morning", "gd morning",
        }
        AFTERNOON_WORDS = {
            "good afternoon", "gud afternoon", "good aftnoon",
            "good afrnoon",
        }
        EVENING_WORDS = {
            "good evening", "gud evening", "good evng",
            "good evning", "gd evening",
        }
        NIGHT_WORDS = {
            "good night", "gud night", "gn", "good nite",
            "gud nite", "goodnite", "goodnight",
        }
        THANKS_WORDS = {
            "thanks", "thank you", "thankyou", "thx", "thnx",
            "thanks a lot", "thank u", "ty", "tq", "many thanks",
            "thanks so much", "thank you so much", "tysm",
            "thank you very much", "thnks", "thnak you",
        }
        BYE_WORDS = {
            "bye", "byee", "byeee", "goodbye", "good bye",
            "see you", "see ya", "take care", "later",
            "ok bye", "okay bye", "cya", "cu later", "ttyl",
            "have a good day", "have a nice day",
        }

        # Fuzzy greeting check — catches typos like "helo", "heloo"
        def fuzzy_greet(text, word_set, threshold=85):
            if text in word_set:
                return True
            # Only fuzzy-match short inputs (avoid false matches on long queries)
            if len(text.split()) <= 3:
                for word in word_set:
                    if fuzz.ratio(text, word) >= threshold:
                        return True
            return False

        if fuzzy_greet(query_lower, GREETING_WORDS):
            return ChatResponse(response="Hi! How can I help you today?")

        if fuzzy_greet(query_lower, MORNING_WORDS):
            return ChatResponse(response="Good Morning! How can I assist you today?")

        if fuzzy_greet(query_lower, AFTERNOON_WORDS):
            return ChatResponse(response="Good Afternoon! How can I assist you today?")

        if fuzzy_greet(query_lower, EVENING_WORDS):
            return ChatResponse(response="Good Evening! How can I assist you today?")

        if fuzzy_greet(query_lower, NIGHT_WORDS):
            return ChatResponse(response="Good Night! Have a pleasant rest. Feel free to reach out anytime.")

        if fuzzy_greet(query_lower, THANKS_WORDS):
            return ChatResponse(response="You're welcome! Let me know if you need anything else.")

        if fuzzy_greet(query_lower, BYE_WORDS):
            return ChatResponse(response="Goodbye! Have a great day ahead. Feel free to come back anytime.")

        # ==========================================
        # Ticket flow — reads from SQLite
        # ==========================================

        pending = db_get_pending(session_id)

        if pending:
            if pending["stage"] == "confirm":
                if query_lower == "yes":
                    db_set_pending(session_id, pending["issue"], pending["category"], "details")
                    return ChatResponse(
                        response=(
                            "Please provide your details to complete the ticket:\n\n"
                            "Format:  Name  |  Employee ID  |  Department\n\n"
                            "Example: John | EMP-1042 | HR"
                        ),
                        status="ticket_details"
                    )
                if query_lower == "no":
                    db_delete_pending(session_id)
                    return ChatResponse(response="Ticket creation cancelled.")
                return ChatResponse(
                    response="Please reply YES to raise a ticket or NO to cancel.",
                    status="ticket_prompt"
                )

            if pending["stage"] == "details":
                if query_lower == "cancel":
                    db_delete_pending(session_id)
                    return ChatResponse(response="Ticket creation cancelled.")

                details = parse_employee_details(refine_query)
                if details is None:
                    return ChatResponse(
                        response=(
                            "I couldn't read that format. Please reply in this exact format:\n\n"
                            "Name  |  Employee ID  |  Department\n\n"
                            "Example: John | EMP-1042 | HR\n\n"
                            "Or type CANCEL to abort."
                        ),
                        status="ticket_details"
                    )

                category  = pending["category"]  # IT / HR / Finance / General
                ticket_id = category[:2].upper() + "-" + str(uuid.uuid4())[:8].upper()
                issue     = pending["issue"]
                now       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                priority  = detect_priority(issue)

                ticket = {
                    "ticket_id":      ticket_id,
                    "issue":          issue,
                    "category":       category,
                    "status":         "Open",
                    "priority":       priority,
                    "employee_name":  details["employee_name"],
                    "employee_id":    details["employee_id"],
                    "department":     details["department"],
                    "session_id":     session_id,
                    "created_at":     now,
                    "updated_at":     now,
                }
                db_insert_ticket(ticket)
                db_delete_pending(session_id)

                return ChatResponse(
                    response=(
                        f"✅ Ticket Created Successfully\n\n"
                        f"Ticket ID   : {ticket_id}\n"
                        f"Issue       : {issue}\n"
                        f"Category    : {category}\n"
                        f"Priority    : {priority}\n"
                        f"Status      : Open\n"
                        f"Name        : {details['employee_name']}\n"
                        f"Employee ID : {details['employee_id']}\n"
                        f"Department  : {details['department']}\n"
                        f"Created At  : {now}\n\n"
                        f"Our IT team will contact you shortly."
                    )
                )

        # ==========================================
        # Department Issue Detection — IT, HR,
        # Finance, General — with fuzzy typo support
        # ==========================================

        DEPARTMENT_KEYWORDS = {
            "IT": [
                "issue", "problem", "error", "failed", "failure",
                "unable", "cannot", "can't", "not working",
                "overheating", "slow laptop", "blue screen",
                "laptop issue", "desktop issue",
                "vpn not connecting", "wifi not working",
                "network issue", "internet issue", "disconnecting",
                "outlook not syncing", "outlook issue",
                "software crash", "application crash", "not responding",
                "cannot print", "printer issue", "printer not working",
                "login failed", "account locked", "access denied",
                "permission issue", "computer issue", "system error",
                "keyboard not working", "mouse not working", "monitor issue",
            ],
            "HR": [
                "leave request", "leave application", "leave balance",
                "salary issue", "salary not received", "payslip",
                "appraisal issue", "performance review",
                "harassment", "complaint", "grievance",
                "attendance issue", "attendance correction",
                "offer letter", "relieving letter", "experience letter",
                "joining issue", "onboarding issue", "resignation",
                "transfer request", "promotion issue",
                "medical claim", "insurance issue",
            ],
            "Finance": [
                    "reimbursement rejected",
                    "expense not approved",
                    "payment not received",
                    "invoice issue",
                    "vendor payment issue",
                    "tax issue",
                    "payroll issue",
                    "salary not credited",
                    "claim rejected",
                    "advance request issue",
                    "budget issue",
                    "purchase order issue"
            ],  
            "General": [
                "canteen issue", "cafeteria issue", "cafeteria not working",
                "parking issue", "parking not available",
                "transport issue", "cab not available", "bus not available",
                "id card issue", "access card issue", "badge issue",
                "id card not working", "access denied to building",
                "housekeeping issue", "maintenance issue",
                "ac not working", "ac issue", "temperature issue",
                "lift issue", "elevator not working",
                "washroom issue", "toilet issue",
                "drinking water issue", "water cooler not working",
            ],
        }

        def fuzzy_keyword_match(text: str, keywords: list) -> bool:
            """Returns True if text matches any keyword — exact or fuzzy."""
            # Exact match first (fast)
            for kw in keywords:
                if text == kw:
                    return True
            # Fuzzy match for typos
            words = text.split()
            for kw in keywords:
                kw_words = kw.split()
                if len(kw_words) == 1:
                    # Single-word keyword — compare against each word
                    for word in words:
                        if len(word) > 3 and fuzz.ratio(word, kw) >= 80:
                            return True
                else:
                    # Multi-word keyword — compare against full query
                    if fuzz.ratio(kw, text) >= 90:
                        return True
            return False

        # ==========================================
        # Only trigger ticket flow if the query
        # looks like a PROBLEM, not a question.
        # "how do i book a meeting room" → RAG
        # "meeting room not working" → ticket
        # ==========================================
        INFORMATIONAL_PREFIXES = (
            "how do i", "how to", "how can i", "how do we",
            "what is", "what are", "what's", "whats",
            "where is", "where are", "where can",
            "when is", "when are", "when will", "when do",
            "who is", "who are", "who can", "who do",
            "can i", "can you", "could you", "please tell",
            "tell me", "explain", "what should i",
            "is there", "do we have", "does hexaware","why",
            "which","list","show me","give me",
        )
        # Always use lowercased query for all detection
        query_lower_stripped = query_lower.strip()

        is_informational = any(
            query_lower_stripped.startswith(prefix)
            for prefix in INFORMATIONAL_PREFIXES
        )

        detected_dept = None
        if not is_informational and len(query_lower_stripped) >= 4:
            # Minimum 4 chars to prevent "ho", "HO", "hi" from
            # triggering department detection
            for dept, keywords in DEPARTMENT_KEYWORDS.items():
                if fuzzy_keyword_match(query_lower_stripped, keywords):
                    detected_dept = dept
                    break

        if detected_dept:
            db_set_pending(session_id, refine_query, detected_dept, "confirm")
            dept_labels = {
                "IT":      "a technical issue",
                "HR":      "an HR-related issue",
                "Finance": "a Finance-related issue",
                "General": "a general facility issue",
            }
            return ChatResponse(
                response=(
                    f"I detected {dept_labels[detected_dept]}.\n\n"
                    f"Issue:\n{refine_query}\n\n"
                    f"Would you like to raise a {detected_dept} support ticket?\n\n"
                    f"Reply YES or NO"
                ),
                status="ticket_prompt"
            )

        # ==========================================
        # Smart Memory — only use history for
        # genuine follow-up words (he, she, it, that)
        # Fresh questions always use only current query
        # to prevent history polluting domain detection
        # ==========================================

        FOLLOW_UP_STARTERS = [
            "he ", "she ", "they ", "them ",
            "that ", "this ", "those ",
            "tell me more", "explain more",
            "what about", "more about", "and what",
            "when is it", "how is it", "what is it",
        ]
        is_follow_up = any(
            query_lower.startswith(word)
            for word in FOLLOW_UP_STARTERS
        )

        if is_follow_up and history:
            # Genuine follow-up — include history for context
            context_query = (
                f"Previous Conversation:\n\n{history[-3:]}\n\n"
                f"Current User Question:\n\n{refine_query}"
            )
        else:
            # Fresh question — use ONLY current query
            # Never mix history into fresh questions
            expanded = expand_query(refine_query)
            context_query = expanded if expanded != refine_query else refine_query

        # ==========================================
        # Agent call with 30-second timeout
        # ==========================================

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    orchestrate.agent_executor.invoke,
                    {"input": context_query}
                ),
                timeout=30.0
            )

            history.append({"user": request.message, "assistant": response.get("output", "")})
            chat_sessions[session_id] = history[-10:]

            output = response.get("output", "")
            if (
                not output
                or output.strip() == ""
                or "no relevant" in output.lower()
                or "couldn't find" in output.lower()
                or "don't have information" in output.lower()
                or "i don't know" in output.lower()
                or "not found" in output.lower()
            ):
                output = (
                    "I couldn't find relevant information for your query. "
                    "You can ask me about HR policies, IT support, Finance, or company information."
                )

            return ChatResponse(response=output)

        except asyncio.TimeoutError:
            print(f"Agent timeout for session {session_id}")
            return ChatResponse(
                response="Sorry, the request took too long. Please try again.",
                status="error"
            )

        except Exception as agent_error:
            print(f"Agent error: {agent_error}")
            return ChatResponse(response=f"Agent Error: {str(agent_error)}", status="error")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Collections
# ==========================================

@app.get("/api/collections")
async def list_collections():
    try:
        collections = custom_Agent.vector_database.client.list_collections()
        return {"collections": [c.name for c in collections], "count": len(collections), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/collections/{collection_name}")
async def delete_collection(collection_name: str, auth: bool = Depends(verify_token)):
    try:
        custom_Agent.vector_database.client.delete_collection(collection_name)
        return {"status": "success", "message": f"Collection '{collection_name}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/{session_id}")
async def get_memory(session_id: str):
    return {"session_id": session_id, "history": chat_sessions.get(session_id, [])}


if __name__ == "__main__":
    import uvicorn
    print("Starting RAG Backend Server...")
    print("API will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    uvicorn.run("Backend_server:app", host="0.0.0.0", port=8000, reload=True)