-- Upgrade talent schema for PoC
-- 1. Extend companies table
ALTER TABLE public.companies 
ADD COLUMN IF NOT EXISTS industry text NOT null DEFAULT '',
ADD COLUMN IF NOT EXISTS tagline text NOT null DEFAULT '',
ADD COLUMN IF NOT EXISTS description text NOT null DEFAULT '',
ADD COLUMN IF NOT EXISTS website text NULL,
ADD COLUMN IF NOT EXISTS tech_stack jsonb NOT null DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS hiring_keywords jsonb NOT null DEFAULT '[]'::jsonb;

-- 2. Create poc_chat_transcripts table
CREATE TABLE IF NOT EXISTS public.poc_chat_transcripts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    public_handle text NOT NULL,
    transcript_md text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(student_user_id)
);

-- 3. Indexes
CREATE INDEX IF NOT EXISTS idx_poc_chat_transcripts_student_user_id ON public.poc_chat_transcripts(student_user_id);
CREATE INDEX IF NOT EXISTS idx_poc_chat_transcripts_public_handle ON public.poc_chat_transcripts(public_handle);

-- 4. Enable RLS
ALTER TABLE public.poc_chat_transcripts ENABLE ROW LEVEL SECURITY;

-- 5. Policies
DROP POLICY IF EXISTS "Students can view their own transcripts" ON public.poc_chat_transcripts;
CREATE POLICY "Students can view their own transcripts"
ON public.poc_chat_transcripts
FOR SELECT
TO authenticated
USING (auth.uid() = student_user_id);

-- Note: Seeding and admin operations will use the service_role key to bypass RLS.
