import google.generativeai as genai
import os
import re
import datetime
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Create a model instance
model = genai.GenerativeModel("models/gemini-2.0-pro-exp")



def extract_location(user_input):
    """
    Extracts a location from user input using a simple regex pattern.
    E.g., "What's the weather in Paris?" returns "Paris".
    """
    match = re.search(r"in ([A-Za-z\s]+)", user_input)
    if match:
        return match.group(1).strip()
    return None

def get_weather_data(location):
    """
    Dummy weather function.
    Replace this with an actual API call to get real weather info.
    """
    # For demonstration, always return 25°C.
    return 25

def load_memory(user_id):
    """
    Load conversation history from a JSON file.
    If no memory is found, return an empty list.
    """
    try:
        with open("chat_memory.json", "r", encoding="utf-8") as f:
            all_memory = json.load(f)
        return all_memory.get(user_id, [])
    except FileNotFoundError:
        return []

def save_memory(user_id, conversation_history):
    """
    Save the updated conversation history back to the JSON file.
    """
    try:
        with open("chat_memory.json", "r", encoding="utf-8") as f:
            all_memory = json.load(f)
    except FileNotFoundError:
        all_memory = {}

    all_memory[user_id] = conversation_history
    with open("chat_memory.json", "w", encoding="utf-8") as f:
        json.dump(all_memory, f, indent=4)

def log_conversation(user_input, bot_reply, conversation_history):
    """
    Append a conversation entry to the history and write to log file.
    Each entry contains a timestamp, the user input, and the bot reply.
    """
    timestamp = datetime.datetime.now().isoformat()
    
    # Add to conversation history
    conversation_history.append({
        "timestamp": timestamp,
        "user": user_input,
        "bot": bot_reply
    })
    
    # Also write to log file
    with open("chat_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | User: {user_input} | Bot: {bot_reply}\n")

def chat_with_gemini(user_input, chat):
    """
    Send a message to the Gemini API and get a response.
    """
    try:
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        return f"Oops! I couldn't process that. Error: {str(e)}"

def safe_chat(user_input, conversation_history, chat):
    """
    Fallback chat function that uses Gemini API with error handling.
    """
    try:
        return chat_with_gemini(user_input, chat)
    except Exception as e:
        return "Oops! I couldn't understand that. Could you please rephrase?"

def personalized_chat(user_name, user_input, conversation_history, chat):
    """
    Personalize the chat by including the user's name.
    """
    custom_input = f"{user_name} says: {user_input}"
    return safe_chat(custom_input, conversation_history, chat)

def bot_reply(user_input, conversation_history, chat):
    """
    Decide the bot's reply:
      - If the input mentions "weather", extract the location and return weather info.
      - Otherwise, use safe_chat as a fallback.
    """
    if "weather" in user_input.lower():
        location = extract_location(user_input)
        if location:
            weather = get_weather_data(location)
            reply = f"The weather in {location} is {weather}°C."
        else:
            reply = "Please specify a location to check the weather."
    else:
        reply = safe_chat(user_input, conversation_history, chat)
    return reply

# ---------------------------
# Main Chat Loop
# ---------------------------
def main():
    user_id = "user123"  # In a real application, this would be dynamic per user.
    conversation_history = load_memory(user_id)
    
    # Convert saved conversation history to Gemini API format
    gemini_history = []
    for entry in conversation_history:
        gemini_history.append({"role": "user", "parts": [entry["user"]]})
        gemini_history.append({"role": "model", "parts": [entry["bot"]]})
    
    # Initialize chat with system prompt and previous conversation history
    initial_prompt = {"role": "user", "parts": ["You are a friendly and witty customer support assistant. Always greet the user by name, and crack light jokes occasionally."]}
    
    if gemini_history:
        chat = model.start_chat(history=[initial_prompt] + gemini_history)
        print(f"Loaded {len(conversation_history)} previous messages.")
    else:
        chat = model.start_chat(history=[initial_prompt])
        print("Starting a new conversation.")
    
    print("Welcome to our chatbot! Type 'exit' to quit.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower().strip() == "exit":
            print("Bot: Goodbye!")
            break

        # Generate reply based on input and conversation history (memory)
        reply = bot_reply(user_input, conversation_history, chat)
        log_conversation(user_input, reply, conversation_history)
        print("Bot:", reply)
    
    # Save updated conversation history
    save_memory(user_id, conversation_history)

if __name__ == "__main__":
    main()