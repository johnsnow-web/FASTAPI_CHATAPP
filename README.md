# U Care

A mental health support application leveraging AI and real-time communication.

## Getting Started

Follow these steps to set up and run the U Care application:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd u_care  # Or the name of the cloned directory
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    * **On Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```
    * **On Windows:**
        ```bash
        venv\Scripts\activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Create a `.env` file:**
    Create a file named `.env` in the root directory of the project.

6.  **Add API keys and configurations to `.env`:**
    Add the following environment variables to your `.env` file, replacing the placeholders with your actual keys and values:

    ```dotenv
    GEMINI_API_KEY=YOUR_GEMINI_API_KEY
    PDF_DIRECTORY=./data/pdfs  # Example path to your PDF directory
    PINECONE_API_KEY=YOUR_PINECONE_API_KEY
    PINECONE_INDEX_NAME=your-pinecone-index-name
    PINECONE_ENV=your-pinecone-environment
    DEEPGRAM_API_KEY=YOUR_DEEPGRAM_API_KEY
    ```

    **Note:**
    * Replace `YOUR_GEMINI_API_KEY` with your Google Gemini API key.
    * Adjust `PDF_DIRECTORY` to the actual path where you intend to store PDF files for knowledge retrieval (if applicable).
    * Replace `YOUR_PINECONE_API_KEY`, `your-pinecone-index-name`, and `your-pinecone-environment` with your Pinecone API key, index name, and environment, respectively (if using Pinecone).
    * Replace `YOUR_DEEPGRAM_API_KEY` with your Deepgram API key.

7.  **Run the FastAPI server:**
    ```bash
    uvicorn app.main:app --reload
    ```
    This command starts the FastAPI server using `uvicorn`. The `--reload` flag enables automatic reloading of the server when you make code changes.

8.  **Access the application:**
    The server will typically start on `http://127.0.0.1:8000`. Open this address in your web browser to access the application (or the specific port indicated in the terminal output).

**Note on WebSocket Endpoint:**

The real-time communication likely happens over a WebSocket endpoint. Check your application's frontend or any client-side documentation for the specific WebSocket URL (e.g., `ws://127.0.0.1:8000/ws`).

**Further Configuration:**

* You might need to configure other settings within the `app/config/settings.py` file as per your project's requirements.
* If you are using Pinecone for vector storage, ensure your Pinecone index is created and populated with relevant data.
* The `PDF_DIRECTORY` is a placeholder; you'll need to implement the logic for loading and processing PDF files if that's a feature of your application.

Enjoy using U Care!
