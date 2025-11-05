-- Ensure auth.users rows automatically mirror into public.app_users
create or replace function public.sync_app_user_profile()
returns trigger as $$
declare
  meta jsonb := new.raw_user_meta_data;
  full_name text := coalesce(meta ->> 'full_name', new.email, 'Unknown User');
  tier text := coalesce(meta ->> 'tier', 'free');
  raw_age text := meta ->> 'age';
  age_value integer;
  gender text := nullif(meta ->> 'gender', '');
  phone text := coalesce(nullif(new.phone, ''), nullif(meta ->> 'phone', ''));
begin
  begin
    if raw_age is not null and raw_age ~ '^\\d+$' then
      age_value := raw_age::integer;
    end if;
  exception when others then
    age_value := null;
  end;

  if tier not in ('free', 'premium') then
    tier := 'free';
  end if;

  insert into public.app_users (
    auth_user_id,
    email,
    full_name,
    age,
    phone_number,
    gender,
    tier
  ) values (
    new.id,
    coalesce(new.email, ''),
    full_name,
    coalesce(age_value, 0),
    phone,
    gender,
    tier
  )
  on conflict (auth_user_id) do update set
    email = excluded.email,
    full_name = excluded.full_name,
    phone_number = excluded.phone_number,
    gender = excluded.gender,
    tier = excluded.tier,
    age = case
      when excluded.age is distinct from public.app_users.age and excluded.age <> 0 then excluded.age
      else public.app_users.age
    end,
    updated_at = timezone('utc', now());

  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_sync_app_user_profile_insert on auth.users;
create trigger trg_sync_app_user_profile_insert
  after insert on auth.users
  for each row
  execute function public.sync_app_user_profile();

drop trigger if exists trg_sync_app_user_profile_update on auth.users;
create trigger trg_sync_app_user_profile_update
  after update on auth.users
  for each row
  when (
    new.email is distinct from old.email or
    new.phone is distinct from old.phone or
    coalesce(new.raw_user_meta_data, '{}'::jsonb) is distinct from coalesce(old.raw_user_meta_data, '{}'::jsonb)
  )
  execute function public.sync_app_user_profile();

-- Backfill any existing auth users missing a profile.
insert into public.app_users (
  auth_user_id,
  email,
  full_name,
  age,
  phone_number,
  gender,
  tier
)
select
  u.id,
  coalesce(u.email, ''),
  coalesce(u.raw_user_meta_data ->> 'full_name', u.email, 'Unknown User'),
  coalesce(
    case
      when (u.raw_user_meta_data ->> 'age') ~ '^\\d+$'
        then (u.raw_user_meta_data ->> 'age')::integer
    end,
    0
  ),
  nullif(coalesce(u.phone, u.raw_user_meta_data ->> 'phone'), ''),
  nullif(u.raw_user_meta_data ->> 'gender', ''),
  case
    when (u.raw_user_meta_data ->> 'tier') in ('free', 'premium')
      then u.raw_user_meta_data ->> 'tier'
    else 'free'
  end
from auth.users u
where not exists (
  select 1 from public.app_users a where a.auth_user_id = u.id
);
