from agent.faq_agent import FAQAgent
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Get the absolute path to the FAQ file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    faq_path = os.path.join(current_dir, "data", "faq.json")
    
    # Get Google API credentials from environment variables
    google_api_key = os.getenv('GOOGLE_API_KEY')
    google_cse_id = os.getenv('GOOGLE_CSE_ID')

    print(f"FAQ Path: {faq_path}")
    print(f"Google API Key: {google_api_key}")
    print(f"Google CSE ID: {google_cse_id}")
    
    if not google_api_key or not google_cse_id:
        raise ValueError("Google API credentials not found in environment variables")
    
    # Initialize the agent with your FAQ data and Google API credentials
    agent = FAQAgent(faq_path, google_api_key, google_cse_id)
    
    print("FAQ Agent initialized. Type 'quit' to exit.")
    
    while True:
        question = input("Ask a question: ")
        if question.lower() == 'quit':
            break
            
        answer = agent.answer_question(question)
        print(f"Answer: {answer}\n")

if __name__ == "__main__":
    main() 