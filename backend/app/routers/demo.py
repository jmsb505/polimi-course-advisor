from typing import List, Set
from fastapi import APIRouter, HTTPException, Query
from ...core.supabase_client import get_supabase
from ...core.text_utils import tokenize, tokens_from_phrase
from pydantic import BaseModel

router = APIRouter(
    prefix="/demo",
    tags=["demo"],
)

class DemoCompany(BaseModel):
    id: str
    name: str
    industry: str
    tagline: str

class RankedCandidate(BaseModel):
    public_handle: str
    skills: List[str]
    interests: List[str]
    goals: List[str]
    preferred_roles: List[str]
    language_preferences: List[str]
    score: float
    matched_terms: List[str]

@router.get("/companies", response_model=List[DemoCompany])
async def list_demo_companies():
    """
    List the 3 seeded companies for the demo.
    """
    supabase = get_supabase()
    # We filter by the specific names seeded in scripts/seed_poc.py
    seed_names = ["Nebula Games Studio", "CloudNode Systems", "Aether AI Research"]
    res = supabase.table("companies").select("id, name, industry, tagline").in_("name", seed_names).execute()
    return res.data

def compute_match_score(
    student_tokens: Set[str],
    student_skills: List[str],
    tech_stack_tokens: Set[str],
    keyword_tokens: Set[str],
    req_skills: List[str],
    context_tokens: Set[str]
):
    """
    Refined heuristic matching:
    - Tech Stack & Keywords: High value hits.
    - Required Skills: Large fixed boosts.
    - Context (Description/Industry): Base coverage.
    """
    score = 0.0
    matched = set()
    
    s_skills_lower = [s.lower() for s in student_skills]
    
    # 1. Required Skills Boost (Max 0.6)
    unique_req_matched = 0
    unique_reqs = set(s.lower() for s in req_skills)
    for rs in unique_reqs:
        if rs in s_skills_lower:
            score += 0.25
            unique_req_matched += 1
            matched.add(rs)
    score = min(score, 0.6) # Cap boost from required skills
    
    # 2. Tech Stack Match (High weight)
    ts_match = tech_stack_tokens.intersection(student_tokens)
    if tech_stack_tokens:
        score += (len(ts_match) / len(tech_stack_tokens)) * 0.3
        matched.update(ts_match)
        
    # 3. Keywords Match (Mid weight)
    kw_match = keyword_tokens.intersection(student_tokens)
    if keyword_tokens:
        score += (len(kw_match) / len(keyword_tokens)) * 0.2
        matched.update(kw_match)
        
    # 4. Context Coverage (Low weight)
    ctx_match = context_tokens.intersection(student_tokens)
    if context_tokens:
        score += (len(ctx_match) / len(context_tokens)) * 0.1
        matched.update(ctx_match)
        
    # Final normalization: Map the accumulated score to a 0-1 range that feels "premium"
    # A single req skill match + some tech stack should easily get to 40-50%.
    # We apply a slight sigmoid-like boost at the low end or just scale up.
    final_score = min(score * 1.5, 0.99)
    
    # If no matches at all, return 0
    if not matched:
        return 0.0, []
        
    return round(final_score, 2), list(matched)[:6]

@router.get("/companies/{company_id}/candidates", response_model=List[RankedCandidate])
async def get_ranked_candidates(company_id: str, top_k: int = 6):
    """
    Fetch and rank candidates for a specific company.
    """
    supabase = get_supabase()
    
    # 1. Fetch company profile and roles
    comp_res = supabase.table("companies").select("industry, description, tech_stack, hiring_keywords").eq("id", company_id).execute()
    if not comp_res.data:
        raise HTTPException(status_code=404, detail="Company not found")
    
    comp = comp_res.data[0]
    roles_res = supabase.table("job_roles").select("title, description, required_skills").eq("company_id", company_id).execute()
    roles = roles_res.data
    
    # 2. Build prioritized token sets
    tech_stack_tokens = set()
    for ts in comp.get("tech_stack", []):
        tech_stack_tokens.update(tokenize(ts))
        
    keyword_tokens = set()
    for kw in comp.get("hiring_keywords", []):
        keyword_tokens.update(tokenize(kw))
        
    context_tokens = set()
    context_tokens.update(tokenize(comp["industry"]))
    context_tokens.update(tokenize(comp["description"]))
    
    all_req_skills = []
    for r in roles:
        # Title is high value, add to tech_stack/keywords effectively
        keyword_tokens.update(tokenize(r["title"]))
        context_tokens.update(tokenize(r["description"]))
        for rs in r.get("required_skills", []):
            all_req_skills.append(rs)
            # Also add to keywords for coverage
            keyword_tokens.update(tokenize(rs))

    # 3. Fetch candidates
    # Rules: Seed students always visible; non-seed only if discoverable.
    seed_handles = ["lunar_dev", "pixel_master", "k8s_navigator", "rust_bucket", "tensor_queen", "data_wizard"]
    
    candidates_res = supabase.table("student_profiles").select("*").execute()
    
    ranked = []
    for s in candidates_res.data:
        is_seed = s["public_handle"] in seed_handles
        if not is_seed and s["visibility"] != "discoverable":
            continue
            
        # Build student token set
        stu_tokens = set()
        for field in ["skills", "interests", "goals", "preferred_roles", "achievements"]:
            val = s.get(field)
            if isinstance(val, list):
                for item in val:
                    stu_tokens.update(tokenize(item))
            elif isinstance(val, str):
                stu_tokens.update(tokenize(val))
        
        score, matches = compute_match_score(
            student_tokens=stu_tokens,
            student_skills=s.get("skills", []),
            tech_stack_tokens=tech_stack_tokens,
            keyword_tokens=keyword_tokens,
            req_skills=all_req_skills,
            context_tokens=context_tokens
        )
        
        ranked.append(RankedCandidate(
            public_handle=s["public_handle"],
            skills=s.get("skills", []),
            interests=s.get("interests", []),
            goals=s.get("goals", []),
            preferred_roles=s.get("preferred_roles", []),
            language_preferences=s.get("language_preferences", []),
            score=score,
            matched_terms=matches
        ))
        
    # 4. Sort and limit
    ranked.sort(key=lambda x: x.score, reverse=True)
    return ranked[:top_k]
