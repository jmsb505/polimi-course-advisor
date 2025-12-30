from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header
from ...core.supabase_client import get_supabase, get_supabase_user_client
from ..schemas_talent import (
    StudentProfileIn, StudentProfileOut, StudentProfilePublic,
    CompanyIn, CompanyOut, JobRoleIn, JobRoleOut,
    IntroRequestIn, IntroRequestOut, IntroRequestUpdate,
    VisibilityUpdate
)

router = APIRouter(
    prefix="/talent",
    tags=["talent"],
)

async def require_user_jwt(authorization: str = Header(...)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format.")
    return authorization.split(" ")[1]

# --- Student Endpoints ---

@router.post("/profile/upsert", response_model=StudentProfileOut)
async def upsert_profile(profile: StudentProfileIn, jwt: str = Depends(require_user_jwt)):
    supabase = get_supabase_user_client(jwt)
    
    user_res = supabase.auth.get_user()
    if not user_res.user:
         raise HTTPException(status_code=401, detail="Invalid or expired token.")
    
    user_id = user_res.user.id
    
    data = profile.model_dump()
    data["user_id"] = user_id
    data["updated_at"] = "now()"
    
    res = supabase.table("student_profiles").upsert(data).execute()
    if not res.data:
        # Map RLS failure or other errors to 403
        raise HTTPException(status_code=403, detail="Permission denied or profile update failed. (RLS)")
    return res.data[0]

@router.post("/profile/visibility", response_model=StudentProfileOut)
async def set_visibility(update: VisibilityUpdate, jwt: str = Depends(require_user_jwt)):
    supabase = get_supabase_user_client(jwt)
    
    user_res = supabase.auth.get_user()
    if not user_res.user:
         raise HTTPException(status_code=401, detail="Invalid or expired token.")
    
    res = supabase.table("student_profiles").update({"visibility": update.visibility}).eq("user_id", user_res.user.id).execute()
    if not res.data:
        raise HTTPException(status_code=403, detail="Permission denied. You can only update your own visibility. (RLS)")
    return res.data[0]

@router.delete("/profile")
async def delete_profile(jwt: str = Depends(require_user_jwt)):
    supabase = get_supabase_user_client(jwt)
    user_res = supabase.auth.get_user()
    if not user_res.user:
         raise HTTPException(status_code=401, detail="Invalid or expired token.")
    
    # RLS should protect this, but we explicitly use the user's ID
    res = supabase.table("student_profiles").delete().eq("user_id", user_res.user.id).execute()
    if not res.data:
        # If the profile didn't exist, it's not strictly an error for a reset, 
        # but RLS might return empty if permission denied.
        return {"status": "already_empty"}
    
    return {"status": "cleared", "deleted_count": len(res.data)}

@router.get("/intro_requests", response_model=List[IntroRequestOut])
async def list_student_intro_requests(jwt: str = Depends(require_user_jwt)):
    supabase = get_supabase_user_client(jwt)
    res = supabase.table("intro_requests").select("*").execute()
    # RLS should naturally filter this to rows where student_user_id = auth.uid()
    return res.data

@router.post("/intro_requests/{request_id}/respond", response_model=IntroRequestOut)
async def respond_to_intro(request_id: str, update: IntroRequestUpdate, jwt: str = Depends(require_user_jwt)):
    supabase = get_supabase_user_client(jwt)
    
    # 1. Update the request status (RLS must enforce that the caller IS the student)
    res = supabase.table("intro_requests").update({"status": update.status}).eq("id", request_id).execute()
    if not res.data:
        raise HTTPException(status_code=403, detail="Intro request not found or permission denied. (RLS)")
    
    updated_req = res.data[0]
    
    # 2. If accepted, create a consent row
    if update.status == "accepted":
        consent_data = {
            "student_user_id": updated_req["student_user_id"],
            "company_id": updated_req["company_id"],
            "job_role_id": updated_req["job_role_id"],
            "scope": ["profile"]
        }
        # We use a user-scoped client for this too; RLS must allow student to create consent for themselves
        supabase.table("consents").insert(consent_data).execute()
        
    return updated_req

# --- Company Endpoints ---

@router.post("/company", response_model=CompanyOut)
async def create_company(company: CompanyIn, jwt: str = Depends(require_user_jwt)):
    supabase = get_supabase_user_client(jwt)
    user_res = supabase.auth.get_user()
    if not user_res.user:
         raise HTTPException(status_code=401, detail="Invalid or expired token.")
    
    data = company.model_dump()
    data["owner_user_id"] = user_res.user.id
    
    res = supabase.table("companies").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=403, detail="Permission denied or company creation failed. (RLS)")
    return res.data[0]

@router.post("/company/{company_id}/roles", response_model=JobRoleOut)
async def create_job_role(company_id: str, role: JobRoleIn, jwt: str = Depends(require_user_jwt)):
    supabase = get_supabase_user_client(jwt)
    data = role.model_dump()
    data["company_id"] = company_id
    
    res = supabase.table("job_roles").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=403, detail="Permission denied. You must own the company to create roles. (RLS)")
    return res.data[0]

@router.get("/company/{company_id}/roles", response_model=List[JobRoleOut])
async def list_company_roles(company_id: str, jwt: str = Depends(require_user_jwt)):
    supabase = get_supabase_user_client(jwt)
    res = supabase.table("job_roles").select("*").eq("company_id", company_id).execute()
    return res.data

@router.get("/candidates", response_model=List[StudentProfilePublic])
async def list_candidates(jwt: str = Depends(require_user_jwt)):
    # Candidates search bypasses row-per-user RLS via admin client but filters strictly.
    # Anyone logged in can see discoverable candidates.
    admin_supabase = get_supabase()
    res = admin_supabase.table("student_profiles").select(
        "public_handle, skills, interests, goals, preferred_roles, language_preferences"
    ).eq("visibility", "discoverable").execute()
    return res.data

@router.post("/company/intro_requests", response_model=IntroRequestOut)
async def request_intro(req: IntroRequestIn, jwt: str = Depends(require_user_jwt)):
    supabase = get_supabase_user_client(jwt)
    admin_supabase = get_supabase()
    
    # 1. Resolve student public_handle to user_id (Admin client needed for this mapping)
    student_res = admin_supabase.table("student_profiles").select("user_id").eq("public_handle", req.student_public_handle).execute()
    if not student_res.data:
        raise HTTPException(status_code=404, detail="Student handle not found.")
    
    student_user_id = student_res.data[0]["user_id"]
    
    # 2. Derive company_id from job_role_id via user client to ensure RLS protection
    # If the user doesn't own the role/company, this select should ideally return empty or be protected.
    role_res = supabase.table("job_roles").select("company_id").eq("id", req.job_role_id).execute()
    if not role_res.data:
        raise HTTPException(status_code=403, detail="Permission denied. You cannot request intros for roles you don't manage. (RLS)")
    
    company_id = role_res.data[0]["company_id"]
    
    # 3. Insert intro request
    data = {
        "company_id": company_id,
        "job_role_id": req.job_role_id,
        "student_user_id": student_user_id,
        "status": "requested"
    }
    
    res = supabase.table("intro_requests").insert(data).execute()
    if not res.data:
         raise HTTPException(status_code=403, detail="Permission denied or request creation failed. (RLS)")
    
    return res.data[0]
