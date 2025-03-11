from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import json
import torch
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, AutoModel
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from datetime import datetime

class FAQAgent:
    def __init__(self, faq_path: str, google_api_key: str, google_cse_id: str):
        self.knowledge_base_path = os.path.dirname(faq_path)
        self.faq_path = faq_path
        self.learned_path = os.path.join(self.knowledge_base_path, "learned_knowledge.json")
        
        # Google Search API credentials
        self.google_api_key = google_api_key
        self.google_cse_id = google_cse_id
        
        # Initialize knowledge bases
        self.faq_knowledge = {}
        self.learned_knowledge = {
            "questions": [],
            "answers": [],
            "embeddings": []
        }
        
        # Load models
        self.qa_model = AutoModelForQuestionAnswering.from_pretrained("bert-large-uncased-whole-word-masking-finetuned-squad")
        self.qa_tokenizer = AutoTokenizer.from_pretrained("bert-large-uncased-whole-word-masking-finetuned-squad")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load knowledge bases
        self.load_faq()
        self.load_learned_knowledge()
        
        # Validate Google API credentials
        self.validate_google_credentials()
    
    def validate_google_credentials(self):
        """Validate Google API credentials with a test search"""
        test_query = "test"
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_api_key,
            'cx': self.google_cse_id,
            'q': test_query,
            'num': 1
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"\nGoogle API Configuration Error:")
                print(f"Status Code: {response.status_code}")
                print(f"Error Message: {error_message}")
                print("\nTo fix this:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Enable the Custom Search API")
                print("3. Enable billing")
                print("4. Verify your API key and Search Engine ID")
                print(f"\nAPI Key: {self.google_api_key[:5]}...{self.google_api_key[-5:]}")
                print(f"Search Engine ID: {self.google_cse_id}")
                raise ValueError("Invalid Google API configuration")
        except Exception as e:
            print(f"Error validating Google credentials: {str(e)}")
            raise
    
    def load_faq(self):
        """Load FAQ data from JSON file"""
        with open(self.faq_path, 'r') as f:
            self.faq_knowledge = json.load(f)
    
    def load_learned_knowledge(self):
        """Load previously learned knowledge"""
        if os.path.exists(self.learned_path):
            with open(self.learned_path, 'r') as f:
                self.learned_knowledge = json.load(f)
                # Convert stored embeddings back to numpy arrays
                self.learned_knowledge["embeddings"] = [
                    np.array(emb) for emb in self.learned_knowledge["embeddings"]
                ]
    
    def save_learned_knowledge(self):
        """Save learned knowledge to file"""
        # Convert numpy arrays to lists for JSON serialization
        save_data = {
            "questions": self.learned_knowledge["questions"],
            "answers": self.learned_knowledge["answers"],
            "embeddings": [emb.tolist() for emb in self.learned_knowledge["embeddings"]]
        }
        with open(self.learned_path, 'w') as f:
            json.dump(save_data, f)
    
    def search_web(self, query: str, num_results: int = 3) -> List[str]:
        """Search the web using Google Custom Search API"""
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_api_key,
            'cx': self.google_cse_id,
            'q': query,
            'num': num_results
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                results = []
                data = response.json()
                
                if 'items' in data:
                    for item in data['items']:
                        # Combine snippet and title for better context
                        text = f"{item.get('title', '')} - {item.get('snippet', '')}"
                        results.append(text)
                    return results
                else:
                    print("No search results found")
                    return []
            else:
                error_message = response.json().get('error', {}).get('message', 'Unknown error')
                print(f"Search API error {response.status_code}: {error_message}")
                print("Please verify:")
                print("1. Custom Search API is enabled in Google Cloud Console")
                print("2. Billing is enabled for your project")
                print("3. API key is correct and has necessary permissions")
                print("4. Search Engine ID (cx) is correct")
                return []
        except Exception as e:
            print(f"Error during web search: {str(e)}")
            return []
    
    def find_similar_question(self, question: str, threshold: float = 0.8) -> tuple:
        """Find similar questions in our knowledge base"""
        if not self.learned_knowledge["questions"]:
            return None, None
        
        # Get embedding for the new question
        question_embedding = self.embedding_model.encode(question)
        
        # Calculate similarities with all stored questions
        similarities = [
            np.dot(question_embedding, stored_emb) / 
            (np.linalg.norm(question_embedding) * np.linalg.norm(stored_emb))
            for stored_emb in self.learned_knowledge["embeddings"]
        ]
        
        max_sim_idx = np.argmax(similarities)
        max_similarity = similarities[max_sim_idx]
        
        if max_similarity >= threshold:
            return (
                self.learned_knowledge["questions"][max_sim_idx],
                self.learned_knowledge["answers"][max_sim_idx]
            )
        return None, None
    
    def learn_from_web(self, question: str, results: List[str]):
        """Learn new information from web search results"""
        if not results:
            return
        
        # Use the first result as the answer (you might want to implement more sophisticated selection)
        answer = results[0]
        
        # Store the new knowledge
        question_embedding = self.embedding_model.encode(question)
        self.learned_knowledge["questions"].append(question)
        self.learned_knowledge["answers"].append(answer)
        self.learned_knowledge["embeddings"].append(question_embedding)
        
        # Save the updated knowledge
        self.save_learned_knowledge()
    
    def answer_question(self, question: str) -> str:
        """Answer user questions based on knowledge base"""
        # First check FAQ file
        for faq in self.faq_knowledge.get('faqs', []):
            # Check for exact or partial matches in questions
            if question.lower() in faq['question'].lower() or faq['question'].lower() in question.lower():
                return faq['answer']
        
        # If no match in FAQ, check learned knowledge for similar questions
        similar_question, stored_answer = self.find_similar_question(question)
        if stored_answer:
            return f"Based on a similar question '{similar_question}', here's the answer: {stored_answer}"
        
        # Only if no local answer is found, search the web
        print("No answer found in FAQ, searching the web...")
        web_results = self.search_web(question)
        
        if web_results:
            # Learn from the web results
            self.learn_from_web(question, web_results)
            return f"I found this answer online: {web_results[0]}"
        
        return "I'm sorry, I couldn't find an answer to your question."

    def _load_faqs(self) -> List[Dict[str, str]]:
        """Load FAQ data from JSON file"""
        try:
            with open(self.faq_path, 'r') as f:
                data = json.load(f)
                return data.get('faqs', [])
        except FileNotFoundError:
            print(f"FAQ file not found: {self.faq_path}")
            return []
        except json.JSONDecodeError:
            print(f"Invalid JSON in FAQ file: {self.faq_path}")
            return []
        except Exception as e:
            print(f"Error loading FAQ file: {str(e)}")
            return [] 