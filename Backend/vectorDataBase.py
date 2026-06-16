import chromadb
import uuid


class vectorDataBase:

    def __init__(self, path_to_store):
        self.client = chromadb.PersistentClient(path_to_store)

    def storeData(
        self,
        vector_embeddings,
        documents,
        indexs=None,
        meta_data=None,
        collection_name=None
    ):
        try:
            collection = self.client.get_or_create_collection(
                collection_name
            )

            if indexs is None:
                indexs = [
                    str(uuid.uuid4())
                    for _ in range(len(vector_embeddings))
                ]

            print(f"Collection : {collection_name}")
            print(f"Documents  : {len(documents)}")
            print(f"Embeddings : {len(vector_embeddings)}")

            # Batch insert to avoid memory issues
            BATCH_SIZE = 50
            total = len(vector_embeddings)

            for i in range(0, total, BATCH_SIZE):

                batch_embeddings = vector_embeddings[i:i + BATCH_SIZE]
                batch_documents = documents[i:i + BATCH_SIZE]
                batch_ids = indexs[i:i + BATCH_SIZE]

                collection.add(
                    embeddings=batch_embeddings,
                    ids=batch_ids,
                    documents=batch_documents
                )

                print(
                    f"Stored batch {i // BATCH_SIZE + 1} "
                    f"({min(i + BATCH_SIZE, total)}/{total} chunks)"
                )

            print(
                f"Successfully added all chunks to "
                f"'{collection_name}'"
            )

        except Exception as e:
            print("Store Data Error:", e)

    def Query(
        self,
        Query_vectors,
        n_result=5,
        collection_name=None
    ):
        """
        Query similar chunks.

        Default = 5 results.
        Better retrieval quality,
        less irrelevant context,
        faster response generation.
        """

        try:
            collection = self.client.get_collection(
                collection_name
            )

            result = collection.query(
                query_embeddings=[Query_vectors],
                n_results=n_result
            )

            return result

        except Exception as e:

            print("Query Error:", e)

            return {
                "documents": [],
                "ids": [],
                "distances": []
            }

    def listCollections(self):
        try:
            collections = self.client.list_collections()
            return [c.name for c in collections]

        except Exception as e:
            print("List Collection Error:", e)
            return []

    def deleteCollection(self, collection_name):
        try:

            self.client.delete_collection(collection_name)

            print(
                f"Collection '{collection_name}' "
                f"deleted successfully."
            )

        except Exception as e:
            print("Delete Collection Error:", e)

    def getCollectionCount(self, collection_name):

        try:

            collection = self.client.get_collection(
                collection_name
            )

            return collection.count()

        except Exception as e:

            print("Count Error:", e)
            return 0

    def replaceCollection(
        self,
        collection_name,
        vector_embeddings,
        documents,
        indexs=None
    ):
        """
        Deletes existing collection
        and recreates it with fresh data.
        """

        try:

            try:

                self.client.delete_collection(
                    collection_name
                )

                print(
                    f"Deleted old collection: "
                    f"{collection_name}"
                )

            except Exception:
                pass

            self.storeData(
                vector_embeddings,
                documents,
                indexs,
                collection_name=collection_name
            )

        except Exception as e:
            print("Replace Collection Error:", e)