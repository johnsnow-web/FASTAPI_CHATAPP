import logging
import time
from langchain_google_genai import GoogleGenerativeAI
from app.services.memory import save_chat_history, get_chat_history
from app.config.settings import GEMINI_API_KEY
# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Initialize Gemini LLM with a more cost-effective model
llm = GoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GEMINI_API_KEY)
llm_checker = GoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GEMINI_API_KEY)

def check_relevance(query, context):
    """Checks if retrieved context is relevant to the user's query using Gemini AI."""
    if not context:
        logging.info("❌ No relevant context found in database.")
        return False

    check_prompt = f"""
    User Query: {query}
    Retrieved Context: {context}

    Is the retrieved context directly relevant and helpful in addressing the user's mental health query?
    Consider the previous conversation history as well.
    - If YES, return **exactly**: "Yes".
    - If NO, return **exactly**: "No".
    """

    start_time = time.time()
    try:
        response = llm_checker.invoke(check_prompt)
        end_time = time.time()
        response_text = response.content.strip().lower() if hasattr(response, "content") else str(response).strip().lower()

        logging.info(f"✅ Relevance check in {end_time - start_time:.2f}s. Relevant: {response_text}")
        return response_text == "yes"
    except Exception as e:
        logging.error(f"❌ Error checking relevance: {e}")
        return False

def generate_response(query, context_prompt=None, chat_history=None):
    """Generates a concise AI response for mental health support."""
    if chat_history is None:
        chat_history = "No previous conversation."

    base_prompt = f"""You are a supportive and concise mental health assistant.
    Understand the user's query and their emotional state.
    **Crucially, use the previous conversation history to maintain context and personalize your responses.**
    Respond in a helpful, empathetic, and brief manner, aiming to address the core of their issue without unnecessary length.

    **Chat History:**
    {chat_history}

    **User Query:**
    {query}

    **AI Response:**"""

    start_time = time.time()
    try:
        if context_prompt:
            if check_relevance(query, context_prompt):
                full_prompt = f"""{base_prompt}

    **Relevant Information:**
    {context_prompt}

    Based on the information above and the chat history, provide a direct and helpful response."""
                response = llm.invoke(full_prompt)
            else:
                full_prompt = f"""{base_prompt}

    Since no specific relevant information was found, use your understanding of mental health and the chat history to provide a brief and supportive response."""
                response = llm.invoke(full_prompt)
        else:
            full_prompt = f"""{base_prompt}

    Provide a brief and supportive response based on your understanding of mental health and the chat history."""
            response = llm.invoke(full_prompt)

        end_time = time.time()
        response_text = response.content.strip() if hasattr(response, "content") else str(response).strip()

        logging.info(f"✅ Response generated in {end_time - start_time:.2f} seconds.")
        logging.info(f"🤖 AI Response: {response_text}")
        return response_text

    except Exception as e:
        logging.error(f"❌ Error generating response: {e}")
        return "I'm sorry, I couldn't process your request right now."

def process_query(user_query, context_retriever):
    """Processes the user query, retrieves context, generates response, and updates memory."""
    logging.info(f"Received query: {user_query}")

    # Get chat history
    chat_history = get_chat_history()
    logging.info(f"Current Chat History:\n{chat_history}")

    # Retrieve context using the provided context_retriever function
    retrieved_context = context_retriever(user_query)
    logging.info(f"Retrieved Context: {retrieved_context}")

    # Generate the AI response, now explicitly passing the chat history
    ai_response = generate_response(user_query, context_prompt=retrieved_context, chat_history=chat_history)

    # Save the interaction to memory
    save_chat_history(user_query, ai_response)
    logging.info("Chat history updated.")

    return ai_response
