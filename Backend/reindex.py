import chromadb
import custom_Agent

client = chromadb.PersistentClient("My_Storage")

# Delete all collections
for n in ["Finance_datas","IT_datas","Company_datas","HR_datas","General_datas"]:
    try:
        client.delete_collection(n)
        print("Deleted:", n)
    except:
        print("Not found:", n)

# Re-index all files
custom_Agent.process_data(r"KnowledgeBase\Finance\Finance knowledge base.txt", "Finance_datas")
custom_Agent.process_data(r"KnowledgeBase\IT\IT_Knowledge_Base.txt", "IT_datas")
custom_Agent.process_data(r"KnowledgeBase\Company\Company profile knowledge base.txt", "Company_datas")
custom_Agent.process_data(r"KnowledgeBase\HR\Hr knowledge base.txt", "HR_datas")
custom_Agent.process_data(r"KnowledgeBase\General\General facilities knowledge base.txt", "General_datas")

print("Done!")