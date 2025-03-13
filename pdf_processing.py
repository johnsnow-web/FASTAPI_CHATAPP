import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PDF_DIRECTORY = os.getenv("PDF_DIRECTORY")

# Function to load all PDFs and split text recursively
def load_and_split_pdfs(directory_path, chunk_size=1000, chunk_overlap=150):
    all_chunks = []

    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    # Get all PDF files from the directory
    pdf_files = [f for f in os.listdir(directory_path) if f.endswith(".pdf")]

    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory_path, pdf_file)
        print(f"Processing: {pdf_path}")

        # Load the PDF using PyPDFLoader
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        # Apply RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,  # Defines chunk size
            chunk_overlap=chunk_overlap,  # Overlapping words to maintain context
            separators=["\n\n", "\n", " ", ""],  # Hierarchical splitting
        )
        chunks = text_splitter.split_documents(documents)
        all_chunks.extend(chunks)

    return all_chunks


def split_text(documents, chunk_size=500, chunk_overlap=50):
    """
    Split documents into smaller chunks using RecursiveCharacterTextSplitter.
    
    :param documents: List of LangChain Document objects
    :param chunk_size: Maximum number of characters per chunk
    :param chunk_overlap: Number of overlapping characters between chunks
    :return: List of split documents
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    split_docs = text_splitter.split_documents(documents)
    return split_docs


if __name__ == "__main__":
    if not PDF_DIRECTORY:
        raise ValueError("PDF_DIRECTORY is not set. Please check your .env file.")

    # Load and process the PDFs
    documents = load_and_split_pdfs(PDF_DIRECTORY)
    split_docs = split_text(documents)
    
    print(f"Total Chunks: {len(split_docs)}")
    print(split_docs[:2])  # Display first two chunks
