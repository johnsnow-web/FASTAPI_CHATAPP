import logging
from langchain_community.vectorstores import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config.settings import GEMINI_API_KEY, PINECONE_INDEX_NAME

# Initialize Pinecone vector store
embed_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)
vector_store = Pinecone.from_existing_index(index_name=PINECONE_INDEX_NAME, embedding=embed_model)

def search_pinecone(query, k=3):
    """Searches Pinecone for similar documents."""
    search_results = vector_store.similarity_search(query, k=k)
    retrieved_contexts = [doc.page_content for doc in search_results if hasattr(doc, "page_content")]
    retrieved_context = "\n".join(retrieved_contexts) if retrieved_contexts else None

    return retrieved_context
