import os
import json
import time
import base64
import logging
from typing import Dict, Optional, Any
import httpx

logger = logging.getLogger(__name__)

class BusinessAuthHandler:
    """
    Handles authentication with business systems.
    Manages tokens, refreshes them when needed, and provides
    authentication headers for API requests.
    """
    
    def __init__(self, business_id: str, auth_config: Dict[str, Any]):
        """
        Initialize the auth handler with business ID and auth configuration.
        
        Args:
            business_id: The ID of the business
            auth_config: Authentication configuration from the integration config
        """
        self.business_id = business_id
        self.auth_config = auth_config
        self.tokens = {}
        self.token_expiry = {}
        
    async def get_auth_headers(self, auth_type: str) -> Dict[str, str]:
        """
        Get authentication headers for the specified auth type.
        
        Args:
            auth_type: The type of authentication (oauth2, api_key, jwt, basic)
            
        Returns:
            Dict containing the appropriate authentication headers
        """
        if auth_type == "oauth2":
            token = await self._get_oauth_token()
            return {"Authorization": f"Bearer {token}"}
        
        elif auth_type == "api_key":
            if not self.auth_config.get("api_key"):
                logger.error(f"API key configuration missing for business {self.business_id}")
                return {}
                
            key = self.auth_config["api_key"]["key"]
            header_name = self.auth_config["api_key"].get("header_name", "X-API-Key")
            return {header_name: key}
            
        elif auth_type == "jwt":
            token = self.auth_config.get("jwt", {}).get("token")
            if not token:
                logger.error(f"JWT token missing for business {self.business_id}")
                return {}
            return {"Authorization": f"Bearer {token}"}
            
        elif auth_type == "basic":
            if not self.auth_config.get("basic"):
                logger.error(f"Basic auth configuration missing for business {self.business_id}")
                return {}
                
            username = self.auth_config["basic"]["username"]
            password = self.auth_config["basic"]["password"]
            auth_string = base64.b64encode(f"{username}:{password}".encode()).decode()
            return {"Authorization": f"Basic {auth_string}"}
            
        return {}
    
    async def _get_oauth_token(self) -> str:
        """
        Get a valid OAuth token, refreshing if necessary.
        
        Returns:
            A valid OAuth access token
        """
        # Check if we have a valid token
        if "oauth2" in self.tokens and not self._is_token_expired("oauth2"):
            return self.tokens["oauth2"]
            
        # Otherwise, refresh the token
        await self._refresh_oauth_token()
        return self.tokens.get("oauth2", "")
    
    def _is_token_expired(self, token_type: str) -> bool:
        """
        Check if a token is expired.
        
        Args:
            token_type: The type of token to check
            
        Returns:
            True if the token is expired or missing, False otherwise
        """
        if token_type not in self.tokens or token_type not in self.token_expiry:
            return True
            
        # Add a 60-second buffer to prevent using tokens that are about to expire
        return time.time() + 60 >= self.token_expiry[token_type]
    
    async def _refresh_oauth_token(self) -> None:
        """
        Refresh the OAuth token using the configured token endpoint.
        """
        if not self.auth_config.get("oauth2"):
            logger.error(f"OAuth2 configuration missing for business {self.business_id}")
            return
            
        oauth_config = self.auth_config["oauth2"]
        token_url = oauth_config["token_url"]
        client_id = oauth_config["client_id"]
        client_secret = oauth_config["client_secret"]
        scopes = " ".join(oauth_config["scopes"])
        grant_type = oauth_config.get("grant_type", "client_credentials")
        
        # Prepare the request
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        data = {
            "grant_type": grant_type,
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        if scopes:
            data["scope"] = scopes
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, headers=headers, data=data)
                if response.status_code != 200:
                    logger.error(f"Failed to refresh OAuth token: {response.text}")
                    return
                    
                token_data = response.json()
                
                # Store the token and its expiry time
                self.tokens["oauth2"] = token_data["access_token"]
                
                # Calculate expiry time (default to 1 hour if not provided)
                expires_in = token_data.get("expires_in", 3600)
                self.token_expiry["oauth2"] = time.time() + expires_in
                
                logger.info(f"OAuth token refreshed for business {self.business_id}")
        except Exception as e:
            logger.error(f"Error refreshing OAuth token: {str(e)}") 