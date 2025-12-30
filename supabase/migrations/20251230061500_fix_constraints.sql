-- Fix constraints for seeding
ALTER TABLE public.companies ADD CONSTRAINT companies_owner_user_id_key UNIQUE (owner_user_id);
ALTER TABLE public.job_roles ADD CONSTRAINT job_roles_company_id_title_key UNIQUE (company_id, title);
