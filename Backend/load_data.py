import custom_Agent

# ==========================================
# Finance Knowledge Base (2 files)
# ==========================================

custom_Agent.process_data(
    r"KnowledgeBase\Finance\Finance_expense_claims.txt",
    "Finance_datas"
)

custom_Agent.process_data(
    r"KnowledgeBase\Finance\Finance salary payroll.txt",
    "Finance_datas"
)

# ==========================================
# IT Knowledge Base
# ==========================================

custom_Agent.process_data(
    r"KnowledgeBase\IT\IT_Knowledge_Base.txt",
    "IT_datas"
)

# ==========================================
# Company Knowledge Base
# ==========================================

custom_Agent.process_data(
    r"KnowledgeBase\Company\Company_profile_knowledge_base.txt",
    "Company_datas"
)

# ==========================================
# HR Knowledge Base
# ==========================================

custom_Agent.process_data(
    r"KnowledgeBase\HR\Hr_knowledge_base.txt",
    "HR_datas"
)

# ==========================================
# General / Facilities Knowledge Base
# ==========================================

custom_Agent.process_data(
    r"KnowledgeBase\General\General facilities knowledge base.txt",
    "General_datas"
)

print("\n====================================")
print("All Knowledge Bases Loaded Successfully!")
print("====================================")