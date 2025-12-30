-- Create extension for UUID generation if it doesn't exist
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1) student_profiles
CREATE TABLE student_profiles (
    user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    public_handle text UNIQUE NOT NULL,
    visibility text NOT NULL DEFAULT 'private' CHECK (visibility IN ('private', 'discoverable')),
    skills jsonb NOT NULL DEFAULT '[]'::jsonb,
    interests jsonb NOT NULL DEFAULT '[]'::jsonb,
    avoid jsonb NOT NULL DEFAULT '[]'::jsonb,
    goals jsonb NOT NULL DEFAULT '[]'::jsonb,
    achievements jsonb NOT NULL DEFAULT '[]'::jsonb,
    portfolio_links jsonb NOT NULL DEFAULT '[]'::jsonb,
    preferred_roles jsonb NOT NULL DEFAULT '[]'::jsonb,
    language_preferences jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- 2) companies
CREATE TABLE companies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 3) job_roles
CREATE TABLE job_roles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title text NOT NULL,
    description text NOT NULL DEFAULT '',
    required_skills jsonb NOT NULL DEFAULT '[]'::jsonb,
    nice_to_have jsonb NOT NULL DEFAULT '[]'::jsonb,
    location text NULL,
    language text NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 4) intro_requests
CREATE TABLE intro_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    job_role_id uuid NOT NULL REFERENCES job_roles(id) ON DELETE CASCADE,
    student_user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'requested' CHECK (status IN ('requested', 'accepted', 'declined')),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(company_id, job_role_id, student_user_id)
);

-- 5) consents
CREATE TABLE consents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    job_role_id uuid NULL REFERENCES job_roles(id) ON DELETE CASCADE,
    scope jsonb NOT NULL DEFAULT '["profile"]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NULL
);

-- Indexes
CREATE INDEX idx_student_profiles_visibility ON student_profiles(visibility);
CREATE INDEX idx_companies_owner_user_id ON companies(owner_user_id);
CREATE INDEX idx_job_roles_company_id ON job_roles(company_id);
CREATE INDEX idx_intro_requests_student_user_id ON intro_requests(student_user_id);
CREATE INDEX idx_intro_requests_company_id ON intro_requests(company_id);
CREATE INDEX idx_consents_student_user_id ON consents(student_user_id);
CREATE INDEX idx_consents_company_id ON consents(company_id);

-- Enable RLS
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE intro_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE consents ENABLE ROW LEVEL SECURITY;

-- student_profiles policies
CREATE POLICY "Users can manage their own profile" ON student_profiles
    FOR ALL USING (auth.uid() = user_id);

-- companies policies
CREATE POLICY "Owners can manage their own companies" ON companies
    FOR ALL USING (auth.uid() = owner_user_id);

-- job_roles policies
CREATE POLICY "Company owners can manage roles" ON job_roles
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM companies
            WHERE companies.id = job_roles.company_id
            AND companies.owner_user_id = auth.uid()
        )
    );

-- intro_requests policies
CREATE POLICY "Students can view their own intro requests" ON intro_requests
    FOR SELECT USING (auth.uid() = student_user_id);

CREATE POLICY "Company owners can view their intro requests" ON intro_requests
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM companies
            WHERE companies.id = intro_requests.company_id
            AND companies.owner_user_id = auth.uid()
        )
    );

-- consents policies
CREATE POLICY "Students can manage their own consents" ON consents
    FOR ALL USING (auth.uid() = student_user_id);

CREATE POLICY "Company owners can view consents for their company" ON consents
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM companies
            WHERE companies.id = consents.company_id
            AND companies.owner_user_id = auth.uid()
        )
    );
