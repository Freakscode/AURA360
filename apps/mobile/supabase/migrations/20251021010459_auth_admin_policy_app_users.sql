-- Ensure Supabase Auth admin role can mirror profiles into app_users.
grant usage on schema public to supabase_auth_admin;

grant select, insert, update, delete on table public.app_users to supabase_auth_admin;
grant usage, select on sequence public.app_users_id_seq to supabase_auth_admin;

create policy "Auth admin manage app_users"
    on public.app_users
    for all
    to supabase_auth_admin
    using (true)
    with check (true);

comment on policy "Auth admin manage app_users" on public.app_users is
    'Allows Supabase Auth admin backend to insert/update mirrored profiles during user creation.';
