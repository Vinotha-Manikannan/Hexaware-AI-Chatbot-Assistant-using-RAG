import chromadb

client = chromadb.PersistentClient("My_Storage")

collections = client.list_collections()

print("\n====================================")
print("ChromaDB Collections Status")
print("====================================")

if not collections:
    print("No collections found — run load_data.py to index files")
else:
    print(f"Total collections: {len(collections)}\n")

    expected = [
        "Finance_datas",
        "IT_datas",
        "Company_datas",
        "HR_datas",
        "General_datas",
    ]

    found_names = []

    for col in collections:
        count = col.count()
        print(f"  ✓ {col.name} — {count} chunks indexed")
        found_names.append(col.name)

    # Check for missing collections
    print("\n------------------------------------")
    missing = [c for c in expected if c not in found_names]
    if missing:
        print("Missing collections (need to index):")
        for m in missing:
            print(f"  ✗ {m}")
        print("\nRun: python load_data.py")
    else:
        print("All 5 collections present ✅")

print("====================================\n")