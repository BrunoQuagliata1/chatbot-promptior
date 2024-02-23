from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from uuid import uuid4
import os


load_dotenv()
client = OpenAI()

pinecone_api_key = os.getenv('PINECONE_API_KEY')
pinecone_index_name = os.getenv('PINECONE_INDEX_NAME')

pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index(pinecone_index_name)

def vectorize_text(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[text],
        encoding_format="float"
    )
    vector = response.data[0].embedding
    return vector


def upsert_to_vector_db(text_data):
    vector = vectorize_text(text_data['content'])
    unique_id = str(uuid4())
    
    data = {
        "id": text_data.get("id", unique_id),
        "vector": vector,
        "metadata": {
            "title": text_data['title'],
            "content": text_data['content'],
            "url": text_data['url'],
            "category": text_data['category'],
        }
    }
    
    index.upsert(vectors=[(data['id'], data['vector'], data['metadata'])])


def query_vector_db(query_vector, top_k=5):
    if not all(isinstance(v, float) for v in query_vector):
        raise ValueError("query_vector must be a list of floats")

    try:
        response = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return []

    documents_content = [match["metadata"]["content"] for match in response["matches"] if "content" in match["metadata"]]

    combined_documents_content = " ".join(documents_content)
    return combined_documents_content

