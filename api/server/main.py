from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import json
import os
from uuid import uuid4
from dotenv import load_dotenv
from datetime import datetime
import requests
import logging
import time
from passlib.context import CryptContext

from src.server.database import SessionLocal, engine, Base
from src.server.models import Business, User, Agent, AgentAction, Conversation, Message
from src.server.schemas import (
    BusinessCreate, BusinessResponse, UserContext, 
    AgentConfig, AgentResponse, UserProfileUpdate, UserSettingsUpdate
)
from src.agent.faq_agent import FAQAgent
from src.agent.task_agent import TaskAgent
from src.agent.auth_handler import BusinessAuthHandler

# Load environment variables
load_dotenv()

# Get and validate environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="Enhanced Agent API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Dependency for database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/business/register", response_model=BusinessResponse)
async def register_business(business: BusinessCreate, db: Session = Depends(get_db)):
    """Register a new business and generate API key"""
    # Check if email already exists
    existing_business = db.query(Business).filter(Business.email == business.email).first()
    if existing_business:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate API key and hash password
    api_key = f"sk_{uuid4().hex}"
    password_hash = pwd_context.hash(business.password)
    
    db_business = Business(
        name=business.name,
        email=business.email,
        password_hash=password_hash,
        api_key=api_key,
        faqs={"faqs": []},
        actions={"actions": {}}
    )
    
    db.add(db_business)
    db.commit()
    db.refresh(db_business)
    
    # Return business details without password hash
    return {
        "id": db_business.id,
        "name": db_business.name,
        "email": db_business.email,
        "api_key": db_business.api_key
    }

@app.post("/business/upload-faq/{api_key}")
async def upload_faq(
    api_key: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload FAQ JSON file for a business"""
    business = db.query(Business).filter(Business.api_key == api_key).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    try:
        contents = await file.read()
        faq_data = json.loads(contents)
        
        # Validate FAQ format
        if not isinstance(faq_data, dict) or "faqs" not in faq_data:
            raise HTTPException(status_code=400, detail="Invalid FAQ format. Must contain 'faqs' array.")
        
        # Update business FAQs in the database
        business.faqs = faq_data
        db.commit()
        
        return {"message": "FAQ data uploaded successfully", "faq_count": len(faq_data["faqs"])}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        logger.error(f"Error uploading FAQ: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/business/upload-actions/{api_key}")
async def upload_actions(
    api_key: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload actions configuration JSON file for a business"""
    business = db.query(Business).filter(Business.api_key == api_key).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    try:
        contents = await file.read()
        actions_data = json.loads(contents)
        
        # Validate actions format
        if not isinstance(actions_data, dict) or "actions" not in actions_data:
            raise HTTPException(status_code=400, detail="Invalid actions format. Must contain 'actions' object.")
        
        # Update business actions in the database
        business.actions = actions_data
        db.commit()
        
        return {"message": "Actions configuration uploaded successfully", "action_count": len(actions_data["actions"])}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        logger.error(f"Error uploading actions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/business/agents/{api_key}", response_model=AgentResponse)
async def create_agent(
    api_key: str,
    agent_config: AgentConfig,
    db: Session = Depends(get_db)
):
    """Create a new agent for a business"""
    business = db.query(Business).filter(Business.api_key == api_key).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Create directory for agent if it doesn't exist
    agent_dir = f"data/businesses/{business.id}/agents"
    os.makedirs(agent_dir, exist_ok=True)
    
    # Generate agent ID
    agent_id = f"agent_{uuid4().hex}"
    
    # Save agent configuration
    config_path = f"{agent_dir}/{agent_id}.json"
    with open(config_path, "w") as f:
        json.dump(agent_config.dict(), f)
    
    # Create agent record in database
    db_agent = Agent(
        id=agent_id,
        name=agent_config.name,
        description=agent_config.description,
        business_id=business.id,
        config_path=config_path
    )
    
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    # Create action records
    for action_id, action_config in agent_config.actions.items():
        db_action = AgentAction(
            id=action_id,
            agent_id=agent_id,
            name=action_config.name,
            description=action_config.description,
            api_endpoint=action_config.api_endpoint,
            method=action_config.method
        )
        db.add(db_action)
    
    db.commit()
    
    return AgentResponse(
        id=db_agent.id,
        name=db_agent.name,
        description=db_agent.description,
        business_id=business.id,
        created_at=db_agent.created_at
    )

@app.get("/business/agents/{api_key}", response_model=List[AgentResponse])
async def list_agents(
    api_key: str,
    db: Session = Depends(get_db)
):
    """List all agents for a business"""
    business = db.query(Business).filter(Business.api_key == api_key).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    agents = db.query(Agent).filter(Agent.business_id == business.id).all()
    return agents

@app.post("/chat/{api_key}")
async def chat(
    api_key: str,
    question: Dict[str, str],
    user_context: Optional[UserContext] = Body(None),
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Process a chat message and return a response.
    Can either answer a question or perform an action based on intent.
    """
    # Validate API key and get business
    business = db.query(Business).filter(Business.api_key == api_key).first()
    if not business:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Get the agent if specified
    if agent_id:
        agent = db.query(Agent).filter(Agent.id == agent_id, Agent.business_id == business.id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
    else:
        # Get the default agent for the business
        agent = db.query(Agent).filter(Agent.business_id == business.id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="No agents found for this business")
    
    # Load agent configuration
    agent_config = json.loads(agent.config)
    
    # Add the business's actions to the agent config
    agent_config.update(business.actions)
    
    logger.info(f"Using FAQs for business {business.id}: {json.dumps(business.faqs)[:200]}...")
    logger.info(f"Using actions for business {business.id}: {json.dumps(business.actions)[:200]}...")
    
    # Create task agent with business's FAQs
    task_agent = TaskAgent(agent_config, business.faqs, business.id)
    
    # Process the question
    text = question.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="No question provided")
    
    # Set default user context if not provided
    if not user_context:
        user_context = UserContext(
            user_id="anonymous",
            permissions=[],
            session_id=f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            metadata={"source": "api"}
        )
    
    # Convert Pydantic model to dict if needed
    user_context_dict = user_context.dict() if hasattr(user_context, "dict") else user_context
    
    # Process the question
    response = await task_agent.process_question(text, user_context_dict)
    
    # Record the conversation in the database
    conversation = db.query(Conversation).filter(
        Conversation.business_id == business.id,
        Conversation.session_id == user_context_dict.get("session_id")
    ).first()
    
    if not conversation:
        conversation = Conversation(
            business_id=business.id,
            user_id=user_context_dict.get("user_id"),
            session_id=user_context_dict.get("session_id"),
            start_time=datetime.now()
        )
        db.add(conversation)
        db.flush()
    
    # Record the message
    message = Message(
        conversation_id=conversation.id,
        text=text,
        is_user=True,
        timestamp=datetime.now()
    )
    db.add(message)
    
    # Record the response
    response_text = response.get("answer", "")
    response_message = Message(
        conversation_id=conversation.id,
        text=response_text,
        is_user=False,
        timestamp=datetime.now(),
        metadata={
            "type": response.get("type"),
            "action": response.get("action"),
            "params": response.get("params"),
            "result": response.get("result")
        }
    )
    db.add(response_message)
    db.commit()
    
    return response

@app.patch("/api/users/profile")
async def update_user_profile(
    user_id: str,
    update: UserProfileUpdate,
    api_key: str,
    db: Session = Depends(get_db)
):
    """
    Update a user's profile in the business's system.
    This endpoint acts as a secure proxy to the business's user management API.
    """
    # Validate API key
    business = db.query(Business).filter(Business.api_key == api_key).first()
    if not business:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Get the default agent for the business to access its configuration
    agent = db.query(Agent).filter(Agent.business_id == business.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="No agents found for this business")
    
    # Load agent configuration
    agent_config = json.loads(agent.config)
    
    # Check if integration is configured
    if not agent_config.get("integration_config"):
        # Fall back to legacy behavior if no integration is configured
        user = db.query(User).filter(User.id == user_id, User.business_id == business.id).first()
        if not user:
            user = User(id=user_id, business_id=business.id)
            db.add(user)
        
        # Update user profile in our database (legacy approach)
        setattr(user, f"profile_{update.field}", update.value)
        db.commit()
        
        # Log the action
        action = AgentAction(
            user_id=user_id,
            business_id=business.id,
            action_type="update_profile",
            parameters={"field": update.field, "value": update.value},
            timestamp=datetime.now()
        )
        db.add(action)
        db.commit()
        
        return {"success": True, "message": f"Profile {update.field} updated successfully"}
    
    # Use the business integration to update the profile
    try:
        # Initialize auth handler
        auth_handler = BusinessAuthHandler(
            business.id, 
            agent_config["integration_config"]["auth"]
        )
        
        # Get data source configuration
        if "user_profiles" not in agent_config["integration_config"]["data_sources"]:
            raise HTTPException(status_code=400, detail="User profiles data source not configured")
            
        data_source = agent_config["integration_config"]["data_sources"]["user_profiles"]
        
        # Get authentication headers
        auth_headers = await auth_handler.get_auth_headers(data_source["auth_type"])
        if not auth_headers and data_source["auth_type"] != "none":
            raise HTTPException(status_code=500, detail="Failed to get authentication headers")
            
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            **auth_headers,
            **(data_source.get("headers", {}))
        }
        
        # Get the endpoint URL
        if "update" not in data_source["methods"].__dict__:
            raise HTTPException(status_code=400, detail="Update method not configured for user profiles")
            
        endpoint_template = data_source["methods"].update
        endpoint = f"{data_source['endpoint']}{endpoint_template}"
        endpoint = endpoint.replace("{user_id}", user_id)
        
        # Map field name if field mappings exist
        field_name = update.field
        field_value = update.value
        
        if ("field_mappings" in agent_config["integration_config"] and 
            "user_profiles" in agent_config["integration_config"]["field_mappings"] and
            update.field in agent_config["integration_config"]["field_mappings"]["user_profiles"]):
            field_name = agent_config["integration_config"]["field_mappings"]["user_profiles"][update.field]
        
        # Prepare request data
        data = {field_name: field_value}
        
        # Execute the request
        async with requests.Session() as session:
            async with session.patch(endpoint, json=data, headers=headers) as response:
                if response.status in (200, 201, 204):
                    # Log the action in our database
                    action = AgentAction(
                        user_id=user_id,
                        business_id=business.id,
                        action_type="update_profile",
                        parameters={"field": update.field, "value": update.value},
                        timestamp=datetime.now()
                    )
                    db.add(action)
                    db.commit()
                    
                    try:
                        result = await response.json()
                        return {"success": True, "message": f"Profile {update.field} updated successfully", "data": result}
                    except:
                        return {"success": True, "message": f"Profile {update.field} updated successfully"}
                else:
                    error_text = await response.text()
                    logger.error(f"Error updating user profile: {error_text}")
                    raise HTTPException(status_code=response.status, detail=f"Error from business API: {error_text}")
    except Exception as e:
        logger.error(f"Exception updating user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/users/settings")
async def update_user_settings(
    user_id: str,
    update: UserSettingsUpdate,
    api_key: str,
    db: Session = Depends(get_db)
):
    """
    Update a user's settings in the business's system.
    This endpoint acts as a secure proxy to the business's settings management API.
    """
    # Validate API key
    business = db.query(Business).filter(Business.api_key == api_key).first()
    if not business:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Get the default agent for the business to access its configuration
    agent = db.query(Agent).filter(Agent.business_id == business.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="No agents found for this business")
    
    # Load agent configuration
    agent_config = json.loads(agent.config)
    
    # Check if integration is configured
    if not agent_config.get("integration_config"):
        # Fall back to legacy behavior if no integration is configured
        user = db.query(User).filter(User.id == user_id, User.business_id == business.id).first()
        if not user:
            user = User(id=user_id, business_id=business.id)
            db.add(user)
        
        # Update user settings in our database (legacy approach)
        setattr(user, f"setting_{update.setting}", update.value)
        db.commit()
        
        # Log the action
        action = AgentAction(
            user_id=user_id,
            business_id=business.id,
            action_type="update_settings",
            parameters={"setting": update.setting, "value": update.value},
            timestamp=datetime.now()
        )
        db.add(action)
        db.commit()
        
        return {"success": True, "message": f"Setting {update.setting} updated successfully"}
    
    # Use the business integration to update the settings
    try:
        # Initialize auth handler
        auth_handler = BusinessAuthHandler(
            business.id, 
            agent_config["integration_config"]["auth"]
        )
        
        # Get data source configuration
        if "user_settings" not in agent_config["integration_config"]["data_sources"]:
            raise HTTPException(status_code=400, detail="User settings data source not configured")
            
        data_source = agent_config["integration_config"]["data_sources"]["user_settings"]
        
        # Get authentication headers
        auth_headers = await auth_handler.get_auth_headers(data_source["auth_type"])
        if not auth_headers and data_source["auth_type"] != "none":
            raise HTTPException(status_code=500, detail="Failed to get authentication headers")
            
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            **auth_headers,
            **(data_source.get("headers", {}))
        }
        
        # Get the endpoint URL
        if "update" not in data_source["methods"].__dict__:
            raise HTTPException(status_code=400, detail="Update method not configured for user settings")
            
        endpoint_template = data_source["methods"].update
        endpoint = f"{data_source['endpoint']}{endpoint_template}"
        endpoint = endpoint.replace("{user_id}", user_id)
        
        # Map field name if field mappings exist
        setting_name = update.setting
        setting_value = update.value
        
        if ("field_mappings" in agent_config["integration_config"] and 
            "user_settings" in agent_config["integration_config"]["field_mappings"] and
            update.setting in agent_config["integration_config"]["field_mappings"]["user_settings"]):
            setting_name = agent_config["integration_config"]["field_mappings"]["user_settings"][update.setting]
        
        # Prepare request data
        data = {setting_name: setting_value}
        
        # Execute the request
        async with requests.Session() as session:
            async with session.patch(endpoint, json=data, headers=headers) as response:
                if response.status in (200, 201, 204):
                    # Log the action in our database
                    action = AgentAction(
                        user_id=user_id,
                        business_id=business.id,
                        action_type="update_settings",
                        parameters={"setting": update.setting, "value": update.value},
                        timestamp=datetime.now()
                    )
                    db.add(action)
                    db.commit()
                    
                    try:
                        result = await response.json()
                        return {"success": True, "message": f"Setting {update.setting} updated successfully", "data": result}
                    except:
                        return {"success": True, "message": f"Setting {update.setting} updated successfully"}
                else:
                    error_text = await response.text()
                    logger.error(f"Error updating user settings: {error_text}")
                    raise HTTPException(status_code=response.status, detail=f"Error from business API: {error_text}")
    except Exception as e:
        logger.error(f"Exception updating user settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/support/transfer")
async def transfer_to_human(
    user_id: str,
    reason: Optional[str] = None,
    priority: str = "medium",
    api_key: str = None,
    db: Session = Depends(get_db)
):
    """
    Transfer a conversation to a human agent in the business's support system.
    This endpoint acts as a secure proxy to the business's support system API.
    """
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
        
    # Validate API key
    business = db.query(Business).filter(Business.api_key == api_key).first()
    if not business:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Get the default agent for the business to access its configuration
    agent = db.query(Agent).filter(Agent.business_id == business.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="No agents found for this business")
    
    # Load agent configuration
    agent_config = json.loads(agent.config)
    
    # Check if integration is configured
    if not agent_config.get("integration_config"):
        # Fall back to legacy behavior if no integration is configured
        # Log the action
        action = AgentAction(
            user_id=user_id,
            business_id=business.id,
            action_type="transfer_to_human",
            parameters={"reason": reason, "priority": priority},
            timestamp=datetime.now()
        )
        db.add(action)
        db.commit()
        
        # For now, we'll just return a success response
        transfer_id = f"TRF{uuid4().hex[:8]}"
        
        return {
            "success": True,
            "message": "Transferring to human agent",
            "transfer_id": transfer_id,
            "estimated_wait_time": "2-5 minutes"
        }
    
    # Use the business integration to create a support ticket
    try:
        # Initialize auth handler
        auth_handler = BusinessAuthHandler(
            business.id, 
            agent_config["integration_config"]["auth"]
        )
        
        # Get data source configuration
        if "support_system" not in agent_config["integration_config"]["data_sources"]:
            raise HTTPException(status_code=400, detail="Support system data source not configured")
            
        data_source = agent_config["integration_config"]["data_sources"]["support_system"]
        
        # Get authentication headers
        auth_headers = await auth_handler.get_auth_headers(data_source["auth_type"])
        if not auth_headers and data_source["auth_type"] != "none":
            raise HTTPException(status_code=500, detail="Failed to get authentication headers")
            
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            **auth_headers,
            **(data_source.get("headers", {}))
        }
        
        # Get the endpoint URL
        if "create" not in data_source["methods"].__dict__:
            raise HTTPException(status_code=400, detail="Create method not configured for support system")
            
        endpoint_template = data_source["methods"].create
        endpoint = f"{data_source['endpoint']}{endpoint_template}"
        
        # Prepare request data
        data = {
            "user_id": user_id,
            "reason": reason or "Customer requested human agent",
            "priority": priority,
            "source": "ai_agent",
            "timestamp": datetime.now().isoformat()
        }
        
        # Execute the request
        async with requests.Session() as session:
            async with session.post(endpoint, json=data, headers=headers) as response:
                if response.status in (200, 201, 204):
                    # Log the action in our database
                    action = AgentAction(
                        user_id=user_id,
                        business_id=business.id,
                        action_type="transfer_to_human",
                        parameters={"reason": reason, "priority": priority},
                        timestamp=datetime.now()
                    )
                    db.add(action)
                    db.commit()
                    
                    try:
                        result = await response.json()
                        return {
                            "success": True,
                            "message": "Transferring to human agent",
                            "transfer_id": result.get("ticket_id", f"TRF{uuid4().hex[:8]}"),
                            "estimated_wait_time": result.get("estimated_wait_time", "2-5 minutes"),
                            "data": result
                        }
                    except:
                        return {
                            "success": True,
                            "message": "Transferring to human agent",
                            "transfer_id": f"TRF{uuid4().hex[:8]}",
                            "estimated_wait_time": "2-5 minutes"
                        }
                else:
                    error_text = await response.text()
                    logger.error(f"Error transferring to human agent: {error_text}")
                    raise HTTPException(status_code=response.status, detail=f"Error from business API: {error_text}")
    except Exception as e:
        logger.error(f"Exception transferring to human agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    return {
        "GOOGLE_API_KEY_SET": bool(GOOGLE_API_KEY),
        "GOOGLE_CSE_ID_SET": bool(GOOGLE_CSE_ID),
        "GOOGLE_API_KEY_LENGTH": len(GOOGLE_API_KEY) if GOOGLE_API_KEY else 0,
        "GOOGLE_CSE_ID_LENGTH": len(GOOGLE_CSE_ID) if GOOGLE_CSE_ID else 0,
        "ENV_FILE_PATH": os.path.abspath('.env'),
        "WORKING_DIR": os.getcwd(),
    }

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Enhanced Agent API", "status": "online"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/business/login")
async def login_business(
    credentials: Dict[str, str],
    db: Session = Depends(get_db)
):
    """Authenticate a business and return their details"""
    email = credentials.get("email")
    password = credentials.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    # Get business by email
    business = db.query(Business).filter(Business.email == email).first()
    if not business:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not pwd_context.verify(password, business.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Return business details without password hash
    return {
        "id": business.id,
        "name": business.name,
        "email": business.email,
        "api_key": business.api_key
    } 