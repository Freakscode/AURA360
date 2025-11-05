-- Add Supabase auth linkage and tier classification to app_users
alter table public.app_users
    add column if not exists auth_user_id uuid,
    add column if not exists tier text;

comment on column public.app_users.auth_user_id is 'Foreign key to auth.users.id for login linkage.';
comment on column public.app_users.tier is 'Membership plan for the user (free or premium).';

-- Ensure plan defaults to free
update public.app_users
set tier = coalesce(tier, 'free');

alter table public.app_users
    alter column tier set not null,
    alter column tier set default 'free';

-- Limit tier values to the enumerated options
alter table public.app_users
    drop constraint if exists app_users_tier_check,
    add constraint app_users_tier_check
        check (tier in ('free', 'premium'));

-- Link any existing rows to auth.users via email
update public.app_users u
set auth_user_id = a.id
from auth.users a
where u.auth_user_id is null
  and lower(u.email) = lower(a.email);

do $$
begin
    if exists (select 1 from public.app_users where auth_user_id is null) then
        raise exception 'app_users.auth_user_id could not be populated. Please set it manually before rerunning this migration.';
    end if;
end;
$$;

alter table public.app_users
    alter column auth_user_id set not null;

create unique index if not exists app_users_auth_user_id_key
    on public.app_users (auth_user_id);

-- Optional helper view for easier joins (id = auth_user_id)
create or replace view public.vw_app_users as
select
    auth_user_id as id,
    full_name,
    age,
    email,
    phone_number,
    gender,
    tier,
    created_at,
    updated_at
from public.app_users;

comment on view public.vw_app_users is 'Projection aligning auth_user_id with id for application queries.';
