import vectorDataBase
import Emedding
from typing import List

embedd = Emedding.Embedding()
vector_database = vectorDataBase.vectorDataBase("My_Storage")

FINANCE_COLLECTION = "Finance_datas"
IT_COLLECTION      = "IT_datas"
COMPANY_COLLECTION = "Company_datas"
HR_COLLECTION      = "HR_datas"
GENERAL_COLLECTION = "General_datas"


def process_data(path: str, collection_name: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()

        if not data:
            print(f"No data found in {path}")
            return

        chunks: List[str] = embedd.getChunks(data)

        if not chunks:
            print("No chunks generated")
            return

        embeddings_vectors: List[List[float]] = []

        for idx, chunk in enumerate(chunks):
            print(f"Embedding Chunk {idx + 1}/{len(chunks)}")
            embeddings_vectors.append(embedd.getEmbeddings(chunk))

        vector_database.storeData(
            embeddings_vectors,
            chunks,
            collection_name=collection_name
        )

        print(f"{collection_name} DONE PROCESS....!!!")

    except Exception as e:
        print("Process Data Error:", e)


def get_related_data(query: str, collection_name: str, n_result: int = 3):
    try:
        q_emb = embedd.getEmbeddings(query)
        return vector_database.Query(q_emb, collection_name=collection_name, n_result=n_result)
    except Exception as e:
        print("Retrieval Error:", e)
        return None
def is_relevant_result(context, threshold=1.2):

    try:

        if not context:
            return False

        distances = context.get("distances", [])

        if not distances:
            return False

        if not distances[0]:
            return False

        best_distance = distances[0][0]

        print("Distances:", distances)
        print("Best Match Distance:", best_distance)

        return best_distance <= threshold

    except Exception as e:
        print("Threshold Error:", e)
        return ("Falseold Error:", e)
        return False


def get_related_data_reranked(query: str, collection_name: str, keywords: list = None):
    """
    Fetches top 15 chunks then reranks them by keyword relevance.
    This fixes cases where vector similarity returns wrong sections.
    """
    try:
        q_emb = embedd.getEmbeddings(query)
        # Fetch more chunks than needed
        result = vector_database.Query(q_emb, collection_name=collection_name, n_result=15)

        if not result or not result.get("documents") or not result["documents"][0]:
            return result

        docs = result["documents"][0]

        if not keywords:
            return result

        # Score each chunk by keyword matches
        def score_chunk(chunk):
            chunk_lower = chunk.lower()
            return sum(1 for kw in keywords if kw.lower() in chunk_lower)

        # Sort by keyword score (highest first), keep top 5
        scored = sorted(enumerate(docs), key=lambda x: score_chunk(x[1]), reverse=True)
        top_indices = [i for i, _ in scored[:5]]
        reranked_docs = [docs[i] for i in top_indices]

        result["documents"][0] = reranked_docs
        return result

    except Exception as e:
        print("Reranked Retrieval Error:", e)
        return None


# ==========================================
# Finance
# ==========================================

def get_finance_datas(query: str):
    print("\n================================")
    print("FINANCE COLLECTION CALLED")
    print("QUERY:", query)
    print("================================\n")

    if not query:
        return "No finance information found."

    try:
        query_lower = query.lower()

        # Query expansion — most specific matches first
        if any(w in query_lower for w in ["credited", "salary credit", "pay date", "when salary", "when is salary", "when credited"]):
            query = "salary credited last working day every month payroll schedule"
        elif any(w in query_lower for w in ["payslip", "pay slip", "salary slip", "download payslip"]):
            query = "payslip download salary slip finance portal"
        elif any(w in query_lower for w in ["submit expense", "expense claim", "claim expense",
                                             "how do i claim", "how to claim", "how do i submit",
                                             "reimbursement", "claim reimbursement"]):
            query = "how do i submit expense reimbursement claim Finance Portal Claims New Expense upload bills"
            # Use reranked retrieval for expense queries
            context = get_related_data_reranked(
    query,
    collection_name=FINANCE_COLLECTION,
    keywords=[
        "expense",
        "claim",
        "reimbursement",
        "portal",
        "submit",
        "upload",
        "bill"
    ]
    )

            if not context:
                return "No finance information found."
            docs = context.get("documents", [])
            if not docs or not docs[0]:
                return "No finance information found."
            print("Finance Documents Retrieved (reranked):", len(docs[0]))
            return "\n\n".join(docs[0])
        elif any(w in query_lower for w in ["expense not approved", "claim rejected", "reimbursement rejected"]):
            query = "reimbursement claim rejected reason correction resubmit"
        elif any(w in query_lower for w in ["bonus", "increment", "hike", "salary increase"]):
            query = "performance bonus salary increment appraisal rating"
        elif any(w in query_lower for w in ["form 16", "tax", "tds", "income tax", "investment declaration"]):
            query = "form 16 TDS income tax investment declaration"
        elif any(w in query_lower for w in ["travel", "per diem", "hotel limit", "travel claim"]):
            query = "travel policy per diem hotel reimbursement domestic international"
        elif any(w in query_lower for w in ["internet bill","wifi bill","communication allowance","mobile bill"]):
            query = ("communication allowance ""internet bill reimbursement ""mobile bill allowance ""monthly claim limit")
        elif any(w in query_lower for w in ["advance", "salary advance", "loan"]):
            query = "salary advance employee loan request eligibility repayment"
        elif any(w in query_lower for w in ["vendor", "invoice", "purchase order"]):
            query = "vendor payment invoice purchase order processing timeline"
        elif any(w in query_lower for w in ["budget", "cost center", "project budget"]):
            query = "budget management cost center project request approval"
        elif any(w in query_lower for w in ["allowance", "meal allowance", "transport allowance"]):
            query = "monthly allowances meal transport communication allowance grade"
        elif any(w in query_lower for w in ["salary structure", "salary component", "ctc", "basic salary"]):
            query = "salary structure components basic HRA special allowance CTC"
        

        context = get_related_data(query, collection_name=FINANCE_COLLECTION)

        if not is_relevant_result(context):
            return "No finance information found."

        if not context:
            return "No finance information found."

        docs = context.get("documents", [])
        if not docs or not docs[0]:
            return "No finance information found."

        print("Finance Documents Retrieved:", len(docs[0]))
        return "\n\n".join(docs[0])

    except Exception as e:
        print("Finance Retrieval Error:", e)
        return "Error retrieving finance information."


# ==========================================
# IT
# ==========================================

def get_IT_datas(query: str):
    print("\n================================")
    print("IT COLLECTION CALLED")
    print("QUERY:", query)
    print("================================\n")

    if not query:
        return "No IT information found."

    try:
        query_lower = query.lower()

        if any(w in query_lower for w in ["vpn", "connect vpn", "vpn error", "vpn not connecting"]):
            query = "VPN setup connection guide GlobalProtect Cisco AnyConnect steps"
        elif any(w in query_lower for w in ["wifi", "wi-fi", "internet", "network", "office wifi"]):
            query = "WiFi network connection office internet setup SSID"
        elif any(w in query_lower for w in ["password", "reset password", "locked", "forgot password", "change password"]):
            query = "password reset self service portal account locked MFA"
        elif any(w in query_lower for w in ["printer", "print", "printing", "cannot print"]):
            query = "printer setup connection printing issue troubleshoot spooler"
        elif any(w in query_lower for w in ["laptop slow", "slow laptop", "performance", "laptop issue", "computer slow"]):
            query = "laptop slow performance issue troubleshoot cleanup restart"
        elif any(w in query_lower for w in ["software", "install", "application", "install software"]):
            query = "software installation request approved applications list"
        elif any(w in query_lower for w in ["email", "outlook", "mailbox", "outlook not syncing"]):
            query = "email outlook mailbox setup configuration issue sync"
        elif any(w in query_lower for w in ["teams", "microsoft teams", "video call", "teams not working"]):
            query = "Microsoft Teams setup meeting video call issue cache"
        elif any(w in query_lower for w in ["onboarding", "new joiner", "first day", "day 1", "joining"]):
            query = "new employee IT onboarding day 1 checklist setup laptop"
        elif any(w in query_lower for w in ["ticket", "raise ticket", "helpdesk", "it support", "support request"]):
            query = "IT helpdesk support ticket raise request portal"
        elif any(w in query_lower for w in ["backup", "data recovery", "deleted file", "recover file"]):
            query = "data backup recovery OneDrive SharePoint recycle bin restore"
        elif any(w in query_lower for w in ["mfa", "authenticator", "two factor", "2fa"]):
            query = "MFA multi factor authentication Microsoft Authenticator setup"
        elif any(w in query_lower for w in ["access", "permission", "access denied", "sharepoint access"]):
            query = "access permissions SharePoint ERP admin rights request"
        elif any(w in query_lower for w in ["device", "new laptop", "laptop request", "hardware request"]):
            query = "new device request laptop hardware procurement workflow"

        context = get_related_data(
            query,
            collection_name=IT_COLLECTION
        )

        if not is_relevant_result(context):
            return "No IT information found."

        if not context:
            return "No IT information found."
        docs = context.get("documents", [])

        if not docs or not docs[0]:
            return "No IT information found."

        print("IT Documents Retrieved:", len(docs[0]))
        return "\n\n".join(docs[0])

    except Exception as e:
        print("IT Retrieval Error:", e)
        return "Error retrieving IT information."


# ==========================================
# Company
# ==========================================

def get_company_datas(query: str):
    print("\n================================")
    print("COMPANY COLLECTION CALLED")
    print("QUERY:", query)
    print("================================\n")

    if not query:
        return "No company information found."

    try:
        query_lower = query.lower()

        if any(w in query_lower for w in ["ceo", "chief executive", "managing director", "who is ceo", "who leads"]):
            query = "CEO Srikrishna Ramakarthikeyan Executive Director name"
        elif any(w in query_lower for w in ["founder", "founded", "started", "history", "established"]):
            query = "Hexaware founder Atul Nishar company history founded 1990"
        elif any(w in query_lower for w in ["chairman"]):
            query = "Hexaware chairman Larry Quinlan leadership board"
        elif any(w in query_lower for w in ["headquarter", "location", "office", "where is hexaware"]):
            query = "Hexaware headquarters Navi Mumbai location offices global"
        elif any(w in query_lower for w in ["employee", "workforce", "staff", "how many people"]):
            query = "Hexaware employees workforce 31000 global headcount"
        elif any(w in query_lower for w in ["revenue", "turnover", "billion", "annual revenue"]):
            query = "Hexaware revenue annual turnover USD billion financial"
        elif any(w in query_lower for w in ["service", "what does hexaware do", "offerings", "what does it do"]):
            query = "Hexaware services AI cloud data digital transformation offerings"
        elif any(w in query_lower for w in ["mission", "vision", "values", "culture", "core values"]):
            query = "Hexaware mission vision values core culture people first"
        elif any(w in query_lower for w in ["career", "job", "hiring", "apply", "opening", "vacancy"]):
            query = "Hexaware careers jobs hiring apply openings recruitment"
        elif any(w in query_lower for w in ["industry", "sector", "client", "serve", "vertical"]):
            query = "Hexaware industries served banking healthcare insurance travel manufacturing"
        elif any(w in query_lower for w in ["award", "recognition", "certified", "great place"]):
            query = "Hexaware awards recognition great place to work certified"
        elif any(w in query_lower for w in ["ownership", "owner", "carlyle", "parent company"]):
            query = "Hexaware ownership Carlyle Group private equity"

        context = get_related_data(
            query,
            collection_name=COMPANY_COLLECTION
        )

        if not is_relevant_result(context):
            return "No company information found."

        if not context:
            return "No company information found."

        docs = context.get("documents", [])
        if not docs or not docs[0]:
            return "No company information found."

        print("Company Documents Retrieved:", len(docs[0]))
        return "\n\n".join(docs[0])

    except Exception as e:
        print("Company Retrieval Error:", e)
        return "Error retrieving company information."


# ==========================================
# HR
# ==========================================

def get_hr_datas(query: str):
    print("\n================================")
    print("HR COLLECTION CALLED")
    print("QUERY:", query)
    print("================================\n")

    if not query:
        return "No HR information found."

    try:
        query_lower = query.lower()

        if any(w in query_lower for w in ["leave", "leaves", "day off", "days off", "annual leave",
                                           "sick leave", "casual leave", "how many leave", "leave days",
                                           "leave balance", "leave entitlement"]):
            query = "leave policy annual sick casual days entitlement balance carry forward"
        elif any(w in query_lower for w in ["wfh", "wff", "work from home", "remote work", "hybrid",
                                             "apply wfh", "wfh policy", "work remotely"]):
            query = "work from home WFH policy eligibility request process days per week"
        elif any(w in query_lower for w in ["salary", "pay", "payroll", "increment", "hike", "salary policy"]):
            query = "salary payroll increment appraisal HR policy structure"
        elif any(w in query_lower for w in ["insurance", "medical", "health", "hospital", "cashless"]):
            query = "medical insurance health coverage cashless hospitalization reimbursement"
        elif any(w in query_lower for w in ["probation", "confirmation", "probation period"]):
            query = "probation period confirmation letter extension policy"
        elif any(w in query_lower for w in ["notice period", "notice", "serving notice"]):
            query = "notice period resignation confirmation probation policy"
        elif any(w in query_lower for w in ["resign", "resignation", "quit", "exit", "last day", "leaving"]):
            query = "resignation exit process notice period full final settlement relieving letter"
        elif any(w in query_lower for w in ["holiday", "public holiday", "national holiday", "holiday list"]):
            query = "holiday list public holidays 2025 company calendar restricted"
        elif any(w in query_lower for w in ["appraisal", "performance review", "rating", "performance cycle"]):
            query = "performance appraisal rating review cycle process timeline"
        elif any(w in query_lower for w in ["pf", "provident fund", "gratuity", "uan", "statutory"]):
            query = "provident fund PF gratuity UAN statutory benefits contribution"
        elif any(w in query_lower for w in ["training", "certification", "learning", "course", "upskill"]):
            query = "training learning development certification reimbursement platform"
        elif any(w in query_lower for w in ["maternity", "paternity", "parental", "baby", "child"]):
            query = "maternity leave paternity leave parental policy weeks days"
        elif any(w in query_lower for w in ["attendance", "timing", "working hours", "office hours", "late arrival"]):
            query = "attendance working hours timing late arrival biometric policy"
        elif any(w in query_lower for w in ["grievance", "complaint", "posh", "harassment", "report"]):
            query = "grievance redressal POSH harassment complaint process ICC"
        elif any(w in query_lower for w in ["bereavement", "marriage leave", "special leave"]):
            query = "bereavement marriage special leave entitlement policy"
        elif any(w in query_lower for w in ["onboarding", "joining", "new employee", "first day"]):
            query = "employee onboarding joining process new hire checklist"
        elif any(w in query_lower for w in ["bonus", "performance bonus", "incentive"]):
            query = "performance bonus incentive annual payout eligibility"
        elif any(w in query_lower for w in ["dress code", "attire", "uniform"]):
            query = "dress code attire office policy formal casual"

        context = get_related_data(
            query,
            collection_name=HR_COLLECTION
        )

        if not is_relevant_result(context):
            return "No HR information found."

        if not context:
            return "No HR information found."
        
        docs = context.get("documents", [])
        if not docs or not docs[0]:
            return "No HR information found."

        print("HR Documents Retrieved:", len(docs[0]))
        return "\n\n".join(docs[0])

    except Exception as e:
        print("HR Retrieval Error:", e)
        return "Error retrieving HR information."


# ==========================================
# General / Facilities
# ==========================================

def get_general_datas(query: str):
    print("\n================================")
    print("GENERAL COLLECTION CALLED")
    print("QUERY:", query)
    print("================================\n")

    if not query:
        return "No facilities information found."

    try:
        query_lower = query.lower()

        if any(w in query_lower for w in ["cafeteria", "canteen", "food", "lunch", "breakfast",
                                           "dinner", "meal", "eating", "snack"]):
            query = "cafeteria food timings meal subsidy cafeteria card menu"
        elif any(w in query_lower for w in ["transport", "bus", "shuttle", "commute", "pickup",
                                             "drop", "route"]):
            query = "company transport bus shuttle route timings registration"
        elif any(w in query_lower for w in ["cab", "taxi", "late night", "working late", "night cab"]):
            query = "cab policy late working night transport home drop request"
        elif any(w in query_lower for w in ["parking", "park", "vehicle", "car park", "two wheeler", "bike"]):
            query = "parking policy vehicle registration office parking sticker"
        elif any(w in query_lower for w in ["meeting room", "conference room", "book room",
                                             "room booking", "book a room"]):
            query = "meeting room booking conference room how to book outlook portal"
        elif any(w in query_lower for w in ["id card", "access card", "badge", "entry card",
                                             "lost id", "replace id"]):
            query = "ID card access card badge lost replacement temporary"
        elif any(w in query_lower for w in ["visitor", "guest", "visitor pass", "invite visitor"]):
            query = "visitor management guest pass registration entry QR code"
        elif any(w in query_lower for w in ["gym", "fitness", "exercise", "workout", "yoga"]):
            query = "office gym fitness facility timings registration trainer"
        elif any(w in query_lower for w in ["fire", "emergency", "evacuation", "safety", "muster"]):
            query = "fire safety emergency evacuation procedure muster point floor warden"
        elif any(w in query_lower for w in ["stationery", "pen", "notebook", "office supply", "printer paper"]):
            query = "stationery office supplies request admin desk bulk order"
        elif any(w in query_lower for w in ["dress code", "attire", "clothing", "formal", "casual friday"]):
            query = "dress code office attire policy formal casual friday permitted"
        elif any(w in query_lower for w in ["ac", "air condition", "temperature", "cold", "hot", "cooling"]):
            query = "AC air conditioning temperature complaint facilities request"
        elif any(w in query_lower for w in ["workstation", "desk", "seating", "chair", "ergonomic"]):
            query = "workstation seating desk ergonomic setup request height adjustable"
        elif any(w in query_lower for w in ["event", "celebration", "birthday", "anniversary", "team outing"]):
            query = "office events celebrations team outing birthday anniversary budget"
        elif any(w in query_lower for w in ["locker", "storage", "personal locker"]):
            query = "locker facility personal storage request floor gym"
        elif any(w in query_lower for w in ["washroom", "toilet", "restroom", "drinking water"]):
            query = "washroom toilet drinking water facilities floor maintenance"
        elif any(w in query_lower for w in ["first aid", "medical room", "nurse", "doctor"]):
            query = "first aid medical room nurse emergency health facility"
        elif any(w in query_lower for w in ["printing", "photocopy", "scan", "scanner"]):
            query = "printing photocopying scanning document office printer floor"

        context = get_related_data(
            query,
            collection_name=GENERAL_COLLECTION
        )

        if not is_relevant_result(context):
            return "No facilities information found."

        if not context:
            return "No facilities information found."

        docs = context.get("documents", [])
        if not docs or not docs[0]:
            return "No facilities information found."

        print("General Documents Retrieved:", len(docs[0]))
        return "\n\n".join(docs[0])

    except Exception as e:
        print("General Retrieval Error:", e)
        return "Error retrieving facilities information."


# ==========================================
# Re-index all knowledge base files
# Run this script directly when files change:
#   python custom_Agent.py
# ==========================================

if __name__ == "__main__":

    # Finance
    process_data(
        r"KnowledgeBase\Finance\Finance knowledge base.txt",
        FINANCE_COLLECTION
    )

    # IT
    process_data(
        r"KnowledgeBase\IT\IT_Knowledge_Base.txt",
        IT_COLLECTION
    )

    # Company
    process_data(
        r"KnowledgeBase\Company\Company profile knowledge base.txt",
        COMPANY_COLLECTION
    )

    # HR
    process_data(
        r"KnowledgeBase\HR\Hr knowledge base.txt",
        HR_COLLECTION
    )

    # General
    process_data(
        r"KnowledgeBase\General\General facilities knowledge base.txt",
        GENERAL_COLLECTION
    )

    print("\nAll Knowledge Bases Loaded Successfully!")