import os
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend/.env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

SHARED_PASSWORD = "PoliMiDemo2025!"

DEMO_DATA = {
    "companies": [
        {
            "email": "owner.gaming@example.com",
            "name": "Nebula Games Studio",
            "industry": "Gaming & Entertainment",
            "tagline": "Crafting immersive universes for the next generation.",
            "description": "Nebula Games is a leading independent studio specializing in high-fidelity RPGs and experimental VR experiences. We leverage AI-driven procedural generation and advanced physics engines.",
            "tech_stack": ["Unreal Engine 5", "C++", "Python", "Lua", "Vulkan"],
            "hiring_keywords": ["Graphics Programming", "Level Design", "Game Physics", "AI for Games"],
            "roles": [
                {
                    "title": "Junior Gameplay Programmer",
                    "description": "Implement core gameplay systems and player interactions in C++.",
                    "required_skills": ["C++", "Data Structures", "Linear Algebra"],
                    "nice_to_have": ["Unreal Engine", "Game Design fundamentals"]
                },
                {
                    "title": "Graphics Engineering Intern",
                    "description": "Assist in optimizing shader pipelines and rendering workflows.",
                    "required_skills": ["C++", "Shaders (HLSL/GLSL)", "Computer Graphics"],
                    "nice_to_have": ["DirectX", "Vulkan"]
                }
            ],
            "students": [
                {
                    "email": "student1.gaming@example.com",
                    "handle": "lunar_dev",
                    "skills": ["C++", "OpenGL", "Python"],
                    "interests": ["Procedural Generation", "Real-time Rendering"],
                    "goals": ["Become a graphics architect"]
                },
                {
                    "email": "student2.gaming@example.com",
                    "handle": "pixel_master",
                    "skills": ["Unreal Engine", "Blueprints", "C#"],
                    "interests": ["Game Design", "Virtual Reality"],
                    "goals": ["Lead a creative team"]
                }
            ]
        },
        {
            "email": "owner.infra@example.com",
            "name": "CloudNode Systems",
            "industry": "Infrastructure & Cloud",
            "tagline": "The backbone of the decentralized web.",
            "description": "CloudNode provides high-performance computing infrastructure and specialized cloud services for data-intensive research. We focus on scalability, security, and energy-efficient data centers.",
            "tech_stack": ["Go", "Kubernetes", "Linux Kernel", "Rust", "Terraform"],
            "hiring_keywords": ["Distributed Systems", "Network Security", "Cloud Architecture", "EBPF"],
            "roles": [
                {
                    "title": "Distributed Systems Developer",
                    "description": "Build resilient and scalable backend services using Go and K8s.",
                    "required_skills": ["Go", "Distributed Computing", "Concurrrency"],
                    "nice_to_have": ["Kubernetes", "gRPC"]
                },
                {
                    "title": "Site Reliability Engineer",
                    "description": "Automate infrastructure deployment and ensure maximum uptime.",
                    "required_skills": ["Linux", "Python", "Cloud Infrastructure"],
                    "nice_to_have": ["Terraform", "Monitoring tools"]
                }
            ],
            "students": [
                {
                    "email": "student1.infra@example.com",
                    "handle": "k8s_navigator",
                    "skills": ["Go", "Linux", "Docker"],
                    "interests": ["Cloud Native", "Networking"],
                    "goals": ["Architect global scale systems"]
                },
                {
                    "email": "student2.infra@example.com",
                    "handle": "rust_bucket",
                    "skills": ["Rust", "Systems Programming", "C"],
                    "interests": ["Operating Systems", "Low-level Backend"],
                    "goals": ["Contribute to open source kernel tools"]
                }
            ]
        },
        {
            "email": "owner.ml@example.com",
            "name": "Aether AI Research",
            "industry": "Artificial Intelligence",
            "tagline": "Decoding intelligence for a better future.",
            "description": "Aether AI is a research-first company building foundational LLMs and computer vision models for scientific discovery. Our mission is to augment human researchers with powerful AI assistants.",
            "tech_stack": ["PyTorch", "Python", "CUDA", "FastAPI", "Transformers"],
            "hiring_keywords": ["Machine Learning", "NLP", "Deep Learning", "Data Engineering"],
            "roles": [
                {
                    "title": "Machine Learning Engineer (Research)",
                    "description": "Train and fine-tune large scale transformer models.",
                    "required_skills": ["PyTorch", "Calculus", "Probability"],
                    "nice_to_have": ["HuggingFace", "NLP experience"]
                },
                {
                    "title": "Data Engineer (ML Pipe)",
                    "description": "Design efficient pipelines for terabyte-scale scientific datasets.",
                    "required_skills": ["Python", "Spark", "SQL"],
                    "nice_to_have": ["Data Lakehouse architectures", "ETL"]
                }
            ],
            "students": [
                {
                    "email": "student1.ml@example.com",
                    "handle": "tensor_queen",
                    "skills": ["Python", "Mathematics", "Machine Learning"],
                    "interests": ["NLP", "Ethics in AI"],
                    "goals": ["AI Research Scientist"]
                },
                {
                    "email": "student2.ml@example.com",
                    "handle": "data_wizard",
                    "skills": ["SQL", "Python", "Pandas"],
                    "interests": ["Big Data", "Visualizations"],
                    "goals": ["Full-stack Data Engineer"]
                }
            ]
        }
    ]
}

def create_user(email):
    # Check if user exists
    # supabase.auth.admin.list_users() is an option but might be slow
    # We'll just try to create and catch "already exists" if possible, 
    # but the simplest for PoC is checking by email via RPC or just trying to create.
    try:
        res = supabase.auth.admin.create_user({
            "email": email,
            "password": SHARED_PASSWORD,
            "email_confirm": True
        })
        return res.user.id
    except Exception as e:
        # Fallback: get user if already exists
        # This is a bit tricky with current SDK version if it doesn't return existing user ID in error
        # Let's use list_users and filter
        users = supabase.auth.admin.list_users()
        for u in users:
            if u.email == email:
                return u.id
        raise Exception(f"Failed to create or find user {email}: {e}")

def seed():
    print("Starting PoC Seeding...")
    
    for comp_data in DEMO_DATA["companies"]:
        print(f"--- Seeding Company: {comp_data['name']} ---")
        owner_id = create_user(comp_data["email"])
        
        # Upsert Company
        company_record = {
            "owner_user_id": owner_id,
            "name": comp_data["name"],
            "industry": comp_data["industry"],
            "tagline": comp_data["tagline"],
            "description": comp_data["description"],
            "tech_stack": comp_data["tech_stack"],
            "hiring_keywords": comp_data["hiring_keywords"]
        }
        
        comp_res = supabase.table("companies").upsert(company_record, on_conflict="owner_user_id").execute()
        company_id = comp_res.data[0]["id"]
        
        # Seed Roles
        for role_data in comp_data["roles"]:
            role_record = {
                "company_id": company_id,
                "title": role_data["title"],
                "description": role_data["description"],
                "required_skills": role_data["required_skills"],
                "nice_to_have": role_data["nice_to_have"]
            }
            supabase.table("job_roles").upsert(role_record, on_conflict="company_id,title").execute()
            
        # Seed Students and Profiles
        for stu_data in comp_data["students"]:
            stu_id = create_user(stu_data["email"])
            
            profile_record = {
                "user_id": stu_id,
                "public_handle": stu_data["handle"],
                "visibility": "discoverable",
                "skills": stu_data["skills"],
                "interests": stu_data["interests"],
                "goals": stu_data["goals"]
            }
            supabase.table("student_profiles").upsert(profile_record, on_conflict="user_id").execute()
            
            # Generate Transcript
            transcript = f"# Chat Transcript for {stu_data['handle']}\n\n"
            transcript += f"**Advisor**: Hi! I'm your course advisor. How can I help you today?\n\n"
            transcript += f"**{stu_data['handle']}**: I'm really interested in {stu_data['interests'][0]} and I'm currently working with {stu_data['skills'][0]}.\n\n"
            transcript += f"**Advisor**: That sounds great! Given your interest in {stu_data['interests'][0]}, I'd recommend looking into courses like 'Advanced {stu_data['interests'][0]}'. What are your long-term goals?\n\n"
            transcript += f"**{stu_data['handle']}**: I want to {stu_data['goals'][0]}.\n\n"
            transcript += f"**Advisor**: Excellent choice. To achieve that, you should focus on building a strong foundation in {stu_data['skills'][0]} and exploring related topics like {comp_data['hiring_keywords'][0]}.\n\n"
            transcript += "---\n*End of PoC Transcript*"
            
            supabase.table("poc_chat_transcripts").upsert({
                "student_user_id": stu_id,
                "public_handle": stu_data["handle"],
                "transcript_md": transcript
            }, on_conflict="student_user_id").execute()

    print("Seeding Complete!")

if __name__ == "__main__":
    seed()
