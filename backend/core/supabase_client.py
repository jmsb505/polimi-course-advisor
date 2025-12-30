import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from the backend/.env file
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

class SupabaseClient:
    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.")
                
            cls._instance = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        return cls._instance

    @classmethod
    def get_user_client(cls, jwt: str) -> Client:
        """
        Create a new client instance with a user's JWT.
        RLS will be enforced based on this user's context.
        """
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set.")
        
        # We create a new client each time because the headers/auth are instance-specific
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        client.postgrest.auth(jwt)
        # Also set the auth header for storage or other services if needed
        client.auth.set_session({"access_token": jwt, "refresh_token": ""})
        return client

# Helper to get the admin client
def get_supabase() -> Client:
    return SupabaseClient.get_client()

# Helper to get a user-scoped client
def get_supabase_user_client(jwt: str) -> Client:
    return SupabaseClient.get_user_client(jwt)
