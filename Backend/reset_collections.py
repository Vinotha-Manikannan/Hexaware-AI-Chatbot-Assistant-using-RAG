import chromadb

client = chromadb.PersistentClient("My_Storage")

collections_to_delete = [
    "Finance_datas",
    "IT_datas"
]

for collection_name in collections_to_delete:
    try:
        client.delete_collection(collection_name)
        print(f"Deleted: {collection_name}")
    except Exception as e:
        print(f"{collection_name} not found")

print("\nReset Complete!")