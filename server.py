import os
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import Pinecone
from langchain_google_genai import GoogleGenerativeAI

# ✅ Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "mental-health-index")

# ✅ Initialize FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# ✅ Set up logging
logging.basicConfig(level=logging.INFO)

# ✅ Initialize Gemini AI Model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GEMINI_API_KEY)

# ✅ Initialize Memory for Chat History
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# ✅ Initialize Pinecone Vector Store
embed_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)
vector_store = Pinecone.from_existing_index(index_name=PINECONE_INDEX_NAME, embedding=embed_model)

def check_relevance(query, context):
    """Uses Gemini to check if retrieved context is relevant to the user's query."""
    llm = GoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GEMINI_API_KEY)

    check_prompt = f"""
    **User Query:** {query}
    **Retrieved Context:** {context}

    **Task:**  
    Determine if the retrieved context fully answers the user's query.
    Respond with only "yes" or "no".
    """

    response = llm.invoke(check_prompt)

    print("in relevance check")

    # ✅ Fix: Ensure response is handled safely
    if hasattr(response, "content"):  
        reply = response.content.strip().lower()  
    elif isinstance(response, str):  
        reply = response.strip().lower()  
    else:  
        reply = str(response).strip().lower()  # Fallback  

    return reply == "yes"


@app.get("/")
async def root():
    return {"message": "Server is running. Go to /static/index.html"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.info("📡 Client connected.")

    try:
        while True:
            user_query = await websocket.receive_text()
            logging.info(f"📩 Received query: {user_query}")

            # Step 1: Search in Pinecone
            search_results = vector_store.similarity_search(user_query, k=3)

            # Step 2: Process Retrieved Context
            retrieved_contexts = [doc.page_content for doc in search_results if hasattr(doc, "page_content")]
            retrieved_context = "\n".join(retrieved_contexts) if retrieved_contexts else None

            # Step 3: Verify if Pinecone context is useful
            if retrieved_context:
                is_relevant = check_relevance(user_query, retrieved_context)
                logging.info("✅ Relevant context found in Pinecone.")
            else:
                logging.info("⚠️ No relevant context found in Pinecone.")
                is_relevant = False

            # Step 4: Decide whether to use Pinecone or Gemini
            if is_relevant:
                logging.info("🔍 Using Pinecone context.")
                context_prompt = f"Use this information to answer accurately:\n\n{retrieved_context}\n\n"
            else:
                logging.info("🧠 Using Gemini's own knowledge.")
                context_prompt = None  # Let Gemini answer freely

            # Step 5: Construct AI Prompt
            prompt = f"""
            You are a knowledgeable AI assistant providing **clear and structured responses**.

            🔹 If **relevant** knowledge exists, use it.  
            🔹 If **not relevant or incomplete**, generate an accurate answer.  
            🔹 **Avoid vague responses** like "I don't know."

            -- **User Query:**  
            {user_query}  

            {"-- **Relevant Data (if available)** --\n" + context_prompt if context_prompt else ""}

            **AI Response:**  
            """

            # Step 6: Generate AI Response
            response = llm.invoke(prompt)

            # Ensure response is handled safely
            if hasattr(response, "content"):  
                ai_reply = response.content  # Extract content safely  
            elif isinstance(response, str):  
                ai_reply = response  # Use response directly if it's a string  
            else:  
                ai_reply = str(response)  # Fallback to string conversion  

            logging.info(f"📤 AI Response: {ai_reply}")



            # Step 7: Store chat history
            memory.save_context({"input": user_query}, {"output": ai_reply})

            # Step 8: Send response to frontend
            await websocket.send_text(ai_reply)
            logging.info(f"📤 Sent AI response: {ai_reply}")

    except WebSocketDisconnect:
        logging.info("🔌 Client disconnected.")
    except Exception as e:
        logging.error(f"❌ Error processing message: {e}")
