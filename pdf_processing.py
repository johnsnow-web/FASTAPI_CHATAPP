import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()
PDF_DIRECTORY = os.getenv("PDF_DIRECTORY")

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


# Function to load all PDFs and split text recursively
def load_and_split_pdfs(directory_path, chunk_size=1000, chunk_overlap=150):
    all_chunks = []

    # Get all PDF files from the directory
    pdf_files = [f for f in os.listdir(directory_path) if f.endswith(".pdf")]

    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory_path, pdf_file)
        print(f"Processing: {pdf_path}")

        # Load the PDF using PyPDFLoader
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()  # ✅ This returns a list of Document objects

        # Apply RecursiveCharacterTextSplitter (use split_documents, not split_text)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],  
        )
        
        chunks = text_splitter.split_documents(documents)  # ✅ Correct method
        all_chunks.extend(chunks)

    return all_chunks


if __name__ == "__main__":
    documents = load_and_split_pdfs(PDF_DIRECTORY)

    # ✅ Check if PDFs are loaded
    if documents:
        print(f"\n✅ Loaded {len(documents)} text chunks successfully.")
        print("\n📜 First 3 Chunks Preview:")
        for chunk in documents[:3]:
            print(chunk)
            print("-" * 50)
    else:
        print("\n⚠️ No documents were loaded! Check PDF directory path.")
