-- ===========================================================================
-- Kinvisit portal schema.
--
-- Run this once in the Supabase SQL editor, on a project created in the
-- ap-south-1 (Mumbai) region. It is written to be re-runnable.
--
-- The rule this file exists to enforce: a family reads its own visits and
-- nothing else, and it is the database that decides that, not the page. Every
-- table has row level security on and no policy grants a blanket read. If the
-- JavaScript in site/assets/js is wrong, or someone opens /records with a
-- session that is not theirs, the query returns zero rows rather than someone
-- else's medical history.
--
-- There is no public sign-up. Accounts are created from the Supabase dashboard
-- or with the service-role key from a trusted machine, never from the browser.
-- ===========================================================================

-- ------------------------------------------------------------------ roles --
-- One row per authenticated user, saying which of the two portals they belong
-- to. A user with no row here can read nothing, which is the safe default for
-- an account that was created but not yet set up.

create table if not exists public.profiles (
  id          uuid primary key references auth.users on delete cascade,
  role        text not null check (role in ('family', 'companion')),
  full_name   text not null default '',
  created_at  timestamptz not null default now()
);

alter table public.profiles enable row level security;

-- Asking "is the caller a companion" from inside a policy on a table that
-- itself has policies would recurse. security definer breaks the cycle, and
-- the empty search_path stops the function resolving a shadowed table.
create or replace function public.is_companion()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role = 'companion'
  );
$$;

drop policy if exists "read own profile" on public.profiles;
create policy "read own profile" on public.profiles
  for select using (id = auth.uid());

-- Nobody writes their own role from the browser. Promoting yourself to
-- companion would hand you every family's records, so role changes happen
-- from the dashboard with the service-role key only.

-- --------------------------------------------------------------- patients --
-- The person who is actually seen in the OPD. family_user_id is the account
-- that may read their record: the son or daughter who booked, usually.

create table if not exists public.patients (
  id              uuid primary key default gen_random_uuid(),
  family_user_id  uuid not null references auth.users on delete cascade,
  name            text not null,
  notes           text not null default '',
  created_at      timestamptz not null default now()
);

create index if not exists patients_family_idx on public.patients (family_user_id);

alter table public.patients enable row level security;

drop policy if exists "family reads own patients" on public.patients;
create policy "family reads own patients" on public.patients
  for select using (family_user_id = auth.uid());

drop policy if exists "companions read patients" on public.patients;
create policy "companions read patients" on public.patients
  for select using (public.is_companion());

drop policy if exists "companions add patients" on public.patients;
create policy "companions add patients" on public.patients
  for insert with check (public.is_companion());

-- ----------------------------------------------------------------- visits --
-- One attended consultation. The scalar columns are the ones the portal lists
-- and filters on; detail holds exactly the shape the desk already produces,
-- so the report renderer needs no translation layer.

create table if not exists public.visits (
  id            uuid primary key default gen_random_uuid(),
  patient_id    uuid not null references public.patients on delete cascade,
  companion_id  uuid not null references auth.users,
  visit_date    date,
  department    text not null default '',
  hospital      text not null default '',
  doctor        text not null default '',
  companion     text not null default '',
  recon         text not null default '',
  next_visit    text not null default '',
  detail        jsonb not null default '{}'::jsonb,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index if not exists visits_patient_idx on public.visits (patient_id, visit_date desc);
create index if not exists visits_companion_idx on public.visits (companion_id);

alter table public.visits enable row level security;

-- A family reaches a visit only through a patient row that names them. This
-- is the policy that matters most in the file.
drop policy if exists "family reads own visits" on public.visits;
create policy "family reads own visits" on public.visits
  for select using (
    exists (
      select 1 from public.patients p
      where p.id = visits.patient_id and p.family_user_id = auth.uid()
    )
  );

drop policy if exists "companions read visits" on public.visits;
create policy "companions read visits" on public.visits
  for select using (public.is_companion());

drop policy if exists "companions write visits" on public.visits;
create policy "companions write visits" on public.visits
  for insert with check (public.is_companion() and companion_id = auth.uid());

-- A companion may correct their own write. They may not quietly rewrite a
-- colleague's record of what a doctor said.
drop policy if exists "companions amend own visits" on public.visits;
create policy "companions amend own visits" on public.visits
  for update using (public.is_companion() and companion_id = auth.uid())
          with check (public.is_companion() and companion_id = auth.uid());

-- Nothing deletes a consultation record. There is no delete policy on this
-- table on purpose: a visit that happened is not something the portal should
-- be able to make disappear.

create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists visits_touch on public.visits;
create trigger visits_touch before update on public.visits
  for each row execute function public.touch_updated_at();

-- ------------------------------------------------------- what a family sees --
-- The count the portal shows. A view inherits the policies of the tables under
-- it, so this leaks nothing that visits does not already allow.

create or replace view public.visit_counts
with (security_invoker = true) as
  select patient_id, count(*)::int as visits, max(visit_date) as last_visit
  from public.visits
  group by patient_id;

-- ===========================================================================
-- Creating accounts, from the dashboard or a trusted machine only:
--
--   1. Authentication > Users > Add user, or invite by email.
--   2. Then, in the SQL editor, give the account a role:
--        insert into public.profiles (id, role, full_name)
--        values ('<the new user uuid>', 'family', 'Name');
--   3. For a family, create the patient they may read:
--        insert into public.patients (family_user_id, name)
--        values ('<the new user uuid>', 'Patient name');
--
-- Turn public sign-up OFF: Authentication > Providers > Email >
-- "Allow new users to sign up" = disabled. Without that, anyone can create an
-- account on your project. They would still read nothing, because a user with
-- no profiles row has no role and every policy above fails closed, but an
-- account you did not issue should not exist at all.
-- ===========================================================================
