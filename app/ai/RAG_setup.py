import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

embed_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

chroma_client = chromadb.PersistentClient(path="./app/ai/my_vector_db")
collection = chroma_client.get_or_create_collection(name="my_texts")

directory_path = "./gitbook"
gitbook_path = Path(directory_path)

md_files = list(gitbook_path.rglob("*.md"))

if not md_files:
    print(f"Не найдено .md файлов в {directory_path}")
    sys.exit(1)

print(f"Найдено {len(md_files)} .md файлов")

text_chunks = []
ids = []

for md_file in md_files:
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        relative_path = str(md_file.relative_to(gitbook_path))
        
        text_chunks.append(content)
        ids.append(relative_path)
        
        print(f"✓ Обработан: {md_file.relative_to(gitbook_path)}")
        
    except Exception as e:
        print(f"✗ Ошибка при обработке {md_file}: {e}")

embeddings = embed_model.encode(text_chunks).tolist()

collection.add(
    documents=text_chunks,
    embeddings=embeddings,
    ids=ids
)

print("База знаний создана!")