import logging
import time
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
from app.config.settings import GEMINI_API_KEY

# Initialize Gemini model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GEMINI_API_KEY)

def check_relevance(query, context):
    """Checks if retrieved context is relevant to the user's query using Gemini AI."""
    if not context:  
        logging.info("❌ No relevant context found in database.")
        return False

    llm_checker = GoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GEMINI_API_KEY)

    check_prompt = f"""
    User Query: {query}
    Retrieved Context: {context}

    Does the retrieved context fully answer the user's query?  
    - If YES, return **exactly**: "Yes".  
    - If NO, return **exactly**: "No".  
    """

    start_time = time.time()
    try:
        response = llm_checker.invoke(check_prompt)
        end_time = time.time()
        response_text = response.content.strip().lower() if hasattr(response, "content") else str(response).strip().lower()

        logging.info(f"✅ Checking relevance completed in {end_time - start_time:.2f} seconds.")
        return response_text == "yes"
    except Exception as e:
        logging.error(f"❌ Error checking relevance: {e}")
        return False

def generate_response(query, context_prompt=None):
    """Generates an AI response with strong priority on database results."""
    full_prompt = f"""
    You are an AI assistant providing structured responses with **high accuracy**.

    **Rules:**
    - **ALWAYS prioritize retrieved database context** over generating new information.  
    - If context **fully answers the query**, use it **as-is**.  
    - If context **partially answers the query**, clearly indicate missing details.  
    - If **no relevant data is found**, say: "I could not find this information in my database."

    **User Query:**  
    {query}  

    {"-- **Retrieved Database Context:** --\n" + context_prompt if context_prompt else ""}

    **AI Response:**  
    """

    start_time = time.time()
    try:
        full_response = llm.invoke(full_prompt)
        end_time = time.time()

        response_text = full_response.content if hasattr(full_response, "content") else str(full_response)
        
        # **Summarize Response**
        summary_prompt = f"""
        Summarize the response in a **concise but complete** manner.

        **Full Response:**
        {response_text}

        **Summarized Response:**  
        """

        summary_start_time = time.time()
        summary_response = llm.invoke(summary_prompt)
        summary_end_time = time.time()

        summary_text = summary_response.content if hasattr(summary_response, "content") else str(summary_response)

        # **Logging**
        logging.info(f"✅ Response generated in {end_time - start_time:.2f} seconds.")
        logging.info(f"✅ Summary generated in {summary_end_time - summary_start_time:.2f} seconds.")

        return summary_text
    except Exception as e:
        logging.error(f"❌ Error generating response: {e}")
        return "I couldn't process your request."
