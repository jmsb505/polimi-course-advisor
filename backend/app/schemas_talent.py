from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# --- Student Profile Schemas ---

class StudentProfileBase(BaseModel):
    public_handle: str
    visibility: Literal["private", "discoverable"] = "private"
    skills: List[str] = []
    interests: List[str] = []
    avoid: List[str] = []
    goals: List[str] = []
    achievements: List[str] = []
    portfolio_links: List[str] = []
    preferred_roles: List[str] = []
    language_preferences: List[str] = []

class StudentProfileIn(StudentProfileBase):
    pass

class StudentProfileOut(StudentProfileBase):
    user_id: str
    created_at: datetime
    updated_at: datetime

class StudentProfilePublic(BaseModel):
    public_handle: str
    skills: List[str]
    interests: List[str]
    goals: List[str]
    preferred_roles: List[str]
    language_preferences: List[str]

class VisibilityUpdate(BaseModel):
    visibility: Literal["private", "discoverable"]

# --- Company Schemas ---

class CompanyIn(BaseModel):
    name: str

class CompanyOut(BaseModel):
    id: str
    owner_user_id: str
    name: str
    created_at: datetime

# --- Job Role Schemas ---

class JobRoleIn(BaseModel):
    title: str
    description: str = ""
    required_skills: List[str] = []
    nice_to_have: List[str] = []
    location: Optional[str] = None
    language: Optional[str] = None

class JobRoleOut(JobRoleIn):
    id: str
    company_id: str
    created_at: datetime

# --- Intro Request Schemas ---

class IntroRequestIn(BaseModel):
    job_role_id: str
    student_public_handle: str

class IntroRequestOut(BaseModel):
    id: str
    company_id: str
    job_role_id: str
    student_user_id: str
    status: Literal["requested", "accepted", "declined"]
    created_at: datetime

class IntroRequestUpdate(BaseModel):
    status: Literal["accepted", "declined"]

# --- Consent Schemas ---

class ConsentOut(BaseModel):
    id: str
    student_user_id: str
    company_id: str
    job_role_id: Optional[str]
    scope: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
