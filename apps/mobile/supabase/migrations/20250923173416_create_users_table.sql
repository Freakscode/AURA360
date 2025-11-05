-- Create application-level users table (distinct from auth.users)
create table if not exists public.app_users (
    id bigserial primary key,
    full_name text not null,
    age integer not null check (age >= 0),
    email text not null,
    phone_number text,
    gender text,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

comment on table public.app_users is 'Application users profile data (separate from auth.users).';
comment on column public.app_users.full_name is 'Full legal name displayed across the app.';
comment on column public.app_users.age is 'Age in years; must be >= 0.';
comment on column public.app_users.email is 'Primary contact email. Must be unique.';
comment on column public.app_users.phone_number is 'Optional phone contact.';
comment on column public.app_users.gender is 'Optional self-identified gender descriptor.';

create unique index if not exists app_users_email_key on public.app_users (lower(email));

alter table public.app_users enable row level security;

create policy "Allow read for authenticated" on public.app_users
    for select
    to authenticated
    using (true);

create policy "Allow insert for authenticated" on public.app_users
    for insert
    to authenticated
    with check (true);

create policy "Service role full access" on public.app_users
    for all
    to service_role
    using (true)
    with check (true);

-- Trigger to keep updated_at fresh
create or replace function public.set_current_timestamp_updated_at()
returns trigger as $$
begin
    new.updated_at = timezone('utc', now());
    return new;
end;
$$ language plpgsql;

create trigger set_app_users_updated_at
    before update on public.app_users
    for each row
    execute procedure public.set_current_timestamp_updated_at();
