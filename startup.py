import os
import logging
from dotenv import load_dotenv
from pdf_processing import load_and_split_pdfs  # Load PDFs and split them
# from vector_store import store_embeddings  # Store embeddings in Pinecone

# Load environment variables
load_dotenv()
PDF_DIRECTORY = os.getenv("PDF_DIRECTORY")

def initialize_pdfs():
    """Load PDFs, split them into chunks, and store embeddings."""
    if not PDF_DIRECTORY:
        logging.error("PDF_DIRECTORY not found in environment variables.")
        return
    
    logging.info("📂 Loading and processing PDFs...")
    
    # Load and split PDFs
    documents = load_and_split_pdfs(PDF_DIRECTORY)

    if not documents:
        logging.warning("⚠️ No documents found!")
        return
    
    logging.info(f"✅ Processed {len(documents)} text chunks.")
    
