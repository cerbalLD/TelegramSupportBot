import os

import chromadb
from sentence_transformers import SentenceTransformer

TRANSFORMER_NAME = os.environ.get("TRANSFORMER_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
DB_RAG_PATH = os.environ.get("DB_RAG_PATH", "./app/ai/my_vector_db")

class RAG():
    def __init__(self):
        self.embed_model = SentenceTransformer(TRANSFORMER_NAME)

        chroma_client = chromadb.PersistentClient(path=DB_RAG_PATH)
        self.collection = chroma_client.get_or_create_collection(name="my_texts")

    def find_relevant_chunks(self, user_query, top_k=3):
        query_embedding = self.embed_model.encode([user_query]).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )

        # results['documents'][0] - список найденных текстов
        # results['distances'][0] - список "расстояний" (меньше = ближе)
        return results['documents'][0]

def main():
    rag = RAG()
    user_question = input("Введите ваш вопрос: ")
    relevant_texts = rag.find_relevant_chunks(user_question)

    print("Найденные релевантные блоки:")
    for i, text in enumerate(relevant_texts):
        print(f"\n--- Блок {i+1} ---")
        print(text[:300] + "...")  
        
if __name__ == "__main__":
    main()