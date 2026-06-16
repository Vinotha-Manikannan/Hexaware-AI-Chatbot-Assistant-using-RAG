from sentence_transformers import SentenceTransformer

class Embedding:

    def __init__(self, Model_name="all-MiniLM-L6-v2"):

        print("Model fetching .....")

        try:
            self.Embedd_Model = SentenceTransformer(
                Model_name,
                local_files_only=True
            )
            print("Loaded model from local cache")

        except Exception:
            print("Local model not found, downloading...")
            self.Embedd_Model = SentenceTransformer(Model_name)

        print("Model fetching Done.....")

    def getChunks(
        self,
        datas,
        chunk_size=1000,   # FIX: increased from 500 → 1000 characters
        over_lap=150,      # FIX: increased from 30 → 150 characters
        Chunk_method=None
    ):
        """
        Splits text into overlapping chunks for embedding.

        chunk_size=1000 : ~150-160 words per chunk
                          Enough to capture full policy sections
                          without losing context

        over_lap=150    : 15% overlap between chunks
                          Ensures answers that span chunk boundaries
                          are still found correctly

        Example with old settings (500/30):
          "Annual Leave: 18 days. Carry forward: max 30 days"
          → may split mid-sentence → incomplete answers

        Example with new settings (1000/150):
          Full policy section stays together → complete answers
        """

        if not datas:
            return []

        print("Chunking data....")

        chunks = []
        text = ""

        for char in datas:
            text += char

            if len(text) >= chunk_size:
                chunks.append(text)
                text = text[-over_lap:]

        if text.strip():
            chunks.append(text)

        print(f"Chunks done.... Total chunks: {len(chunks)}")

        return chunks

    def getEmbeddings(self, datas):

        if not datas:
            return None

        print("Embeddings Begins")

        embedding_vector = self.Embedd_Model.encode(datas).tolist()

        print("Embeddings End")

        return embedding_vector