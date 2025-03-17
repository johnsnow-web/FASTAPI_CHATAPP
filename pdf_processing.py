import os
from pinecone import Pinecone
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Pinecone as PineconeVectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pinecone import ServerlessSpec

# ✅ Load environment variables
load_dotenv()
PDF_DIRECTORY = os.getenv("PDF_DIRECTORY", "./pdfs")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "mental-health-index")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ Initialize Pinecone Client
pc = Pinecone(api_key=PINECONE_API_KEY)

# ✅ Ensure index exists
if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=768,  # Adjust based on the embedding model
        metric="cosine",
        spec=ServerlessSpec(cloud='aws', region='us-east-1')  # Update with your region if needed
    )

# ✅ Load embedding model
embed_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)

def split_text(documents, chunk_size=500, chunk_overlap=50):
    """Splits text into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return text_splitter.split_documents(documents)

def load_and_split_pdfs(directory_path):
    """Loads all PDFs from a directory, extracts and splits text."""
    all_chunks = []
    pdf_files = [f for f in os.listdir(directory_path) if f.endswith(".pdf")]

    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory_path, pdf_file)
        print(f"📄 Processing: {pdf_path}")

        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        chunks = split_text(documents)

        for chunk in chunks:
            chunk.metadata["source"] = pdf_file  # Ensure metadata is correctly added

        all_chunks.extend(chunks)

    return all_chunks

def store_chunks_in_pinecone(chunks):
    """Stores document chunks as vector embeddings in Pinecone."""
    if not chunks:
        print("⚠️ No document chunks found!")
        return

    vector_store = PineconeVectorStore.from_documents(chunks, embed_model, index_name=PINECONE_INDEX_NAME)
    print(f"✅ Successfully stored {len(chunks)} chunks in Pinecone.")

if __name__ == "__main__":
    documents = load_and_split_pdfs(PDF_DIRECTORY)

    if documents:
        print(f"\n✅ Loaded {len(documents)} text chunks successfully.")
        store_chunks_in_pinecone(documents)
    else:
        print("\n⚠️ No documents were loaded! Check the PDF directory path.")
