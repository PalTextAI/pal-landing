from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Dict, List, Any, Optional, Union, Literal
from datetime import datetime
import re

def validate_email(email: str) -> bool:
    """Basic email validation using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

class BusinessCreate(BaseModel):
    name: str
    email: str
    password: str

    @validator('email')
    def validate_email_format(cls, v):
        if not validate_email(v):
            raise ValueError('Invalid email format')
        return v

class BusinessResponse(BaseModel):
    id: int
    name: str
    email: str
    api_key: str

    class Config:
        orm_mode = True

# New schemas for user context and agent configuration
class UserContext(BaseModel):
    user_id: str
    permissions: List[str] = []
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ActionParameter(BaseModel):
    name: str
    type: str
    required: bool
    description: str
    allowed_values: Optional[List[str]] = None
    default: Optional[str] = None

class ActionConfig(BaseModel):
    name: str
    description: str
    required_permissions: List[str] = []
    parameters: List[ActionParameter] = []
    api_endpoint: str
    method: str
    data_source: Optional[str] = None
    operation: Optional[str] = None

class IntentResponse(BaseModel):
    success: str
    failure: str

class IntentConfig(BaseModel):
    name: str
    description: str
    keywords: List[str]
    action: str
    responses: IntentResponse

class DataSourceMethod(BaseModel):
    get: str
    update: Optional[str] = None
    create: Optional[str] = None
    delete: Optional[str] = None

class DataSource(BaseModel):
    type: str = Field(..., pattern="^(api|database|graphql)$")
    endpoint: str
    auth_type: str = Field(..., pattern="^(oauth2|api_key|jwt|basic)$")
    methods: DataSourceMethod
    headers: Optional[Dict[str, str]] = None

class OAuth2Config(BaseModel):
    token_url: str
    client_id: str
    client_secret: str
    scopes: List[str]
    grant_type: str = "client_credentials"

class ApiKeyConfig(BaseModel):
    key: str
    header_name: str = "X-API-Key"

class JWTConfig(BaseModel):
    secret: str
    algorithm: str = "HS256"
    expires_in: int = 3600  # seconds

class BasicAuthConfig(BaseModel):
    username: str
    password: str

class AuthConfig(BaseModel):
    oauth2: Optional[OAuth2Config] = None
    api_key: Optional[ApiKeyConfig] = None
    jwt: Optional[JWTConfig] = None
    basic: Optional[BasicAuthConfig] = None

class ParameterMapping(BaseModel):
    source_field: str
    target_field: str

class IntegrationConfig(BaseModel):
    data_sources: Dict[str, DataSource]
    auth: AuthConfig
    field_mappings: Optional[Dict[str, Dict[str, str]]] = None

class AgentConfig(BaseModel):
    name: str
    description: str
    actions: Dict[str, ActionConfig]
    intents: List[IntentConfig]
    default_response: str
    integration_config: Optional[IntegrationConfig] = None

class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: AgentConfig

class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    business_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class UserProfileUpdate(BaseModel):
    field: str
    value: Any

class UserSettingsUpdate(BaseModel):
    setting: str
    value: Any 