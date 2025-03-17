from langchain.memory import ConversationBufferMemory

# Shared memory instance
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

def save_chat_history(user_query, ai_response):
    """Saves user query and AI response in memory."""
    memory.save_context({"input": user_query}, {"output": ai_response})

def get_chat_history():
    """Fetch stored chat history in a structured format."""
    history_messages = memory.load_memory_variables({}).get("chat_history", [])

    if not history_messages:
        return "No previous conversation."

    formatted_history = []
    
    for message in history_messages:
        if hasattr(message, "content"):
            if message.type == "human":
                formatted_history.append(f"User: {message.content}")
            elif message.type == "ai":
                formatted_history.append(f"AI: {message.content}")

    return "\n".join(formatted_history) if formatted_history else "No previous conversation."
