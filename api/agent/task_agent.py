from typing import Dict, List, Any, Optional, Tuple
import json
import os
import re
import logging
import requests
from datetime import datetime
from .auth_handler import BusinessAuthHandler
from rapidfuzz.distance import Levenshtein
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import httpx

# Simplified NLTK initialization for serverless
nltk_initialized = False

def ensure_nltk_data():
    global nltk_initialized
    if not nltk_initialized:
        # Use a simpler approach for serverless
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk_initialized = True
        except Exception as e:
            logging.error(f"Error initializing NLTK: {str(e)}")

logger = logging.getLogger(__name__)

class TaskAgent:
    """
    Enhanced agent that can answer questions and perform tasks based on
    detected intents and user permissions.
    """
    
    def __init__(self, agent_config: Dict[str, Any], faqs: Dict[str, List], business_id: str):
        """
        Initialize the TaskAgent with configuration and FAQ data.
        
        Args:
            agent_config: Configuration for the agent including intents and actions
            faqs: FAQ data dictionary containing list of questions and answers
            business_id: ID of the business this agent belongs to
        """
        ensure_nltk_data()
        logger.info(f"Initializing TaskAgent for business {business_id}")
        
        self.agent_config = agent_config
        self.business_id = business_id
        self.faqs = self._load_faqs() if faqs else []
        logger.info(f"Loaded {len(self.faqs)} FAQs")
        
        self.http_client = None  # Will be initialized on demand
        self.stop_words = set(stopwords.words('english'))
        
        # Initialize auth handler if auth config is provided
        self.auth_handler = None
        if "auth_config" in agent_config:
            self.auth_handler = BusinessAuthHandler(business_id, agent_config["auth_config"])
        
    def __del__(self):
        """Clean up resources when the agent is destroyed"""
        # No need to close HTTP client as we're using httpx on demand
        pass
    
    def _load_faqs(self) -> List[Dict[str, str]]:
        """
        Load FAQ data from the specified JSON file.
        
        Returns:
            List of FAQ items with questions and answers
        """
        try:
            if not os.path.exists(self.faq_path):
                logger.error(f"FAQ file not found: {self.faq_path}")
                return []
                
            with open(self.faq_path, 'r') as f:
                data = json.load(f)
                
            return data.get('faqs', [])
        except Exception as e:
            logger.error(f"Error loading FAQs: {str(e)}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text by converting to lowercase, removing punctuation and stopwords"""
        # Convert to lowercase and remove punctuation
        text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Tokenize and remove stopwords
        tokens = word_tokenize(text)
        tokens = [t for t in tokens if t not in self.stop_words]
        
        return ' '.join(tokens)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using Levenshtein distance"""
        if not text1 or not text2:
            return 0
        
        # Calculate similarity using Levenshtein ratio
        return Levenshtein.normalized_similarity(text1.lower(), text2.lower())
    
    def detect_intent(self, question: str) -> Tuple[Optional[Dict[str, Any]], float]:
        """Detect the user's intent based on the question using improved text matching"""
        logger.info(f"Detecting intent for question: {question}")
        
        # First check if the question matches any FAQ
        best_faq_match = None
        best_faq_score = 0.0
        
        logger.info(f"Checking against {len(self.faqs)} FAQs")
        for faq in self.faqs:
            # Try exact match first
            if question.lower() == faq['question'].lower():
                logger.info(f"Found exact FAQ match: {faq['question']}")
                return {"type": "faq", "faq": faq}, 1.0
                
            # Then try similarity matching
            similarity = self.calculate_similarity(question, faq['question'])
            logger.info(f"FAQ similarity score {similarity} for: {faq['question']}")
            
            if similarity > best_faq_score:
                best_faq_score = similarity
                best_faq_match = faq
        
        if best_faq_score >= 0.7:  # Lowered threshold from 0.8 to 0.7
            logger.info(f"Found best FAQ match: {best_faq_match['question']} with score: {best_faq_score}")
            return {"type": "faq", "faq": best_faq_match}, best_faq_score
            
        # If no good FAQ match, check intents
        logger.info("No good FAQ match found, checking intents...")
        
        best_intent_match = None
        best_intent_score = 0.0
        
        for intent in self.agent_config['intents']:
            score = self._calculate_intent_match(question, intent)
            logger.info(f"Intent score {score} for: {intent['name']}")
            
            if score > best_intent_score:
                best_intent_score = score
                best_intent_match = intent
        
        # Return the best match if it exceeds the threshold
        if best_intent_score >= 0.6:
            logger.info(f"Found best intent match: {best_intent_match['name']} with score: {best_intent_score}")
            return {"type": "intent", "intent": best_intent_match}, best_intent_score
        
        logger.info("No good matches found")
        return None, 0.0
    
    def _calculate_intent_match(self, question: str, intent: Dict[str, Any]) -> float:
        """Calculate how well a question matches an intent using keyword matching and text similarity"""
        question_lower = self._preprocess_text(question)
        
        # Check for keyword matches
        keyword_matches = 0
        total_keywords = len(intent['keywords'])
        
        for keyword in intent['keywords']:
            keyword_proc = self._preprocess_text(keyword)
            if keyword_proc in question_lower:
                keyword_matches += 1
            else:
                # Check for partial matches using similarity
                for word in question_lower.split():
                    if self.calculate_similarity(word, keyword_proc) >= 0.8:
                        keyword_matches += 0.5
                        break
        
        return min(1.0, keyword_matches / total_keywords)
    
    def extract_parameters(self, question: str, action_id: str) -> Dict[str, Any]:
        """
        Extract parameters for an action from the question.
        
        Args:
            question: The user's question
            action_id: ID of the action to extract parameters for
            
        Returns:
            Dictionary of parameter names and values
        """
        if action_id not in self.agent_config['actions']:
            return {}
            
        action = self.agent_config['actions'][action_id]
        parameters = {}
        
        for param in action['parameters']:
            # Extract parameter based on type
            if param['type'] == 'string':
                # For fields with allowed values, check for those specifically
                if 'allowed_values' in param and param['allowed_values']:
                    for value in param['allowed_values']:
                        if value.lower() in question.lower():
                            parameters[param['name']] = value
                            break
                else:
                    # Generic extraction based on parameter name
                    pattern = rf"{param['name']}[:\s]+([^\s,\.]+)"
                    match = re.search(pattern, question, re.IGNORECASE)
                    if match:
                        parameters[param['name']] = match.group(1)
            
            # Add support for other parameter types as needed
            
            # Use default value if available and parameter not found
            if param['name'] not in parameters and 'default' in param:
                parameters[param['name']] = param['default']
        
        return parameters
    
    def _has_permissions(self, user_context: Dict[str, Any], required_permissions: List[str]) -> bool:
        """
        Check if the user has all required permissions.
        
        Args:
            user_context: Context information about the user
            required_permissions: List of permissions required for an action
            
        Returns:
            True if the user has all required permissions, False otherwise
        """
        if not required_permissions:
            return True
            
        user_permissions = user_context.get('permissions', [])
        return all(perm in user_permissions for perm in required_permissions)
    
    async def execute_action(self, action_id: str, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action with the given parameters.
        
        Args:
            action_id: ID of the action to execute
            parameters: Parameters for the action
            user_context: Context information about the user
            
        Returns:
            Result of the action execution
        """
        # Verify action exists
        if action_id not in self.agent_config['actions']:
            return {"success": False, "message": f"Action {action_id} not found"}
            
        action = self.agent_config['actions'][action_id]
        
        # Check permissions
        if not self._has_permissions(user_context, action['required_permissions']):
            return {"success": False, "message": "Permission denied"}
        
        # Check if we should use business integration
        if self.auth_handler and action.get('data_source') and "integration_config" in self.agent_config:
            return await self._execute_integrated_action(action, parameters, user_context)
        else:
            return await self._execute_standard_action(action, parameters, user_context)
    
    async def _execute_standard_action(self, action: Dict[str, Any], parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action using the standard API endpoint approach.
        
        Args:
            action: The action configuration
            parameters: Parameters for the action
            user_context: Context information about the user
            
        Returns:
            Result of the action execution
        """
        # Prepare the request
        url = action['api_endpoint']
        method = action['method'].upper()
        headers = {"Content-Type": "application/json"}
        
        # Add user context to the request
        data = {
            "parameters": parameters,
            "user_context": user_context
        }
        
        try:
            async with self.http_client.request(method, url, json=data, headers=headers) as response:
                if response.status in (200, 201, 204):
                    result = await response.json()
                    return {"success": True, "message": "Action executed successfully", "data": result}
                else:
                    error_text = await response.text()
                    logger.error(f"Error executing action {action['name']}: {error_text}")
                    return {"success": False, "message": f"Error: {error_text}"}
        except Exception as e:
            logger.error(f"Exception executing action {action['name']}: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def _execute_integrated_action(self, action: Dict[str, Any], parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action that integrates with an external API"""
        integration_config = self.agent_config["integration_config"]
        data_source_name = action.get('data_source')
        
        if data_source_name not in integration_config['data_sources']:
            return {"success": False, "message": f"Data source {data_source_name} not configured"}
            
        data_source = integration_config['data_sources'][data_source_name]
        operation = action.get('operation', 'update')
        
        if operation not in data_source['methods'].__dict__:
            return {"success": False, "message": f"Operation {operation} not supported by data source {data_source_name}"}
            
        # Get the endpoint URL
        endpoint_template = getattr(data_source['methods'], operation)
        endpoint = f"{data_source['endpoint']}{endpoint_template}"
        
        # Replace path parameters
        for key, value in user_context.items():
            endpoint = endpoint.replace(f"{{{key}}}", str(value))
            
        # Get authentication headers
        auth_headers = await self.auth_handler.get_auth_headers(data_source['auth_type'])
        if not auth_headers and data_source['auth_type'] != "none":
            return {"success": False, "message": "Failed to get authentication headers"}
            
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            **auth_headers,
            **(data_source.get('headers', {}))
        }
        
        # Map parameters to business-specific field names if mappings exist
        mapped_params = {}
        if 'field_mappings' in integration_config and data_source_name in integration_config['field_mappings']:
            field_mappings = integration_config['field_mappings'][data_source_name]
            
            for param_name, param_value in parameters.items():
                if param_name in field_mappings:
                    mapped_params[field_mappings[param_name]] = param_value
                else:
                    mapped_params[param_name] = param_value
        else:
            mapped_params = parameters
            
        # Execute the request
        method = action['method'].upper()
        
        try:
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(endpoint, params=mapped_params, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(endpoint, json=mapped_params, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(endpoint, json=mapped_params, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(endpoint, headers=headers)
                elif method.upper() == "PATCH":
                    response = await client.patch(endpoint, json=mapped_params, headers=headers)
                else:
                    return {"error": f"Unsupported HTTP method: {method}"}
                
                # Process the response
                if response.status_code >= 200 and response.status_code < 300:
                    response_data = response.json() if response.text else {}
                    
                    # Map the response to the output format
                    result = {}
                    if 'response_mapping' in action:
                        for output_field, response_field in action['response_mapping'].items():
                            if "." in response_field:
                                # Handle nested fields
                                parts = response_field.split(".")
                                value = response_data
                                for part in parts:
                                    if isinstance(value, dict) and part in value:
                                        value = value[part]
                                    else:
                                        value = None
                                        break
                                result[output_field] = value
                            else:
                                result[output_field] = response_data.get(response_field)
                    else:
                        # If no mapping is provided, return the entire response
                        result = response_data
                    
                    return result
                else:
                    error_message = f"API request failed with status {response.status_code}"
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict) and "error" in error_data:
                            error_message = error_data["error"]
                    except:
                        error_message = response.text or error_message
                    
                    return {"error": error_message}
        except Exception as e:
            logger.error(f"Error executing integrated action: {str(e)}")
            return {"error": f"Failed to execute action: {str(e)}"}
    
    async def process_question(self, question: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user question and return an answer or execute an action.
        
        Args:
            question: The user's question
            user_context: Context information about the user
            
        Returns:
            Response with answer or action result
        """
        # Detect intent
        intent_match, confidence = self.detect_intent(question)
        
        if not intent_match:
            # No intent matched, return default response
            return {
                "type": "answer",
                "answer": self.agent_config['default_response'],
                "confidence": 0.0
            }
            
        if intent_match['type'] == 'faq':
            # Return the FAQ answer
            return {
                "type": "answer",
                "answer": intent_match['faq']['answer'],
                "source": "faq",
                "confidence": confidence
            }
            
        # Handle intent that maps to an action
        intent = intent_match['intent']
        action_id = intent['action']
        
        # Extract parameters for the action
        parameters = self.extract_parameters(question, action_id)
        
        # Execute the action
        action_result = await self.execute_action(action_id, parameters, user_context)
        
        # Return the result
        if action_result['success']:
            return {
                "type": "action",
                "action": action_id,
                "answer": intent['responses']['success'],
                "params": parameters,
                "result": action_result,
                "confidence": confidence
            }
        else:
            return {
                "type": "action",
                "action": action_id,
                "answer": intent['responses']['failure'],
                "params": parameters,
                "result": action_result,
                "confidence": confidence
            } 