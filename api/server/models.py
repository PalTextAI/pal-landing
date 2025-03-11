from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Business(Base):
    __tablename__ = "businesses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)  # Store hashed password
    api_key = Column(String, unique=True, index=True)
    faqs = Column(JSON, default={"faqs": []})  # Store FAQs directly in the database
    actions = Column(JSON, default={"actions": {}})  # Store actions configuration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Add relationships
    agents = relationship("Agent", back_populates="business")
    users = relationship("User", back_populates="business")

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    config_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    business = relationship("Business", back_populates="agents")
    actions = relationship("AgentAction", back_populates="agent")

class AgentAction(Base):
    __tablename__ = "agent_actions"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    name = Column(String)
    description = Column(String, nullable=True)
    api_endpoint = Column(String)
    method = Column(String)
    
    agent = relationship("Agent", back_populates="actions")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    profile = Column(JSON, default={})
    settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    business = relationship("Business", back_populates="users")
    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    is_user = Column(Integer, default=1)  # 1 for user, 0 for agent
    text = Column(Text)
    action_taken = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    conversation = relationship("Conversation", back_populates="messages") 