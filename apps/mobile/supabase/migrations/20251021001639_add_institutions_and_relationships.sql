-- Extend user profiles with role/billing metadata to support institutional contexts.
alter table public.app_users
    add column if not exists role_global text,
    add column if not exists is_independent boolean not null default false,
    add column if not exists billing_plan text;

comment on column public.app_users.role_global is 'Rol primario a nivel sistema (referencia rápida, memberships guardan el detalle).';
comment on column public.app_users.is_independent is 'Identifica si el usuario opera fuera de instituciones (B2C).';
comment on column public.app_users.billing_plan is 'Código del plan comercial asignado (individual, corporate, etc.).';

update public.app_users
set
    role_global = coalesce(nullif(role_global, ''), 'General'),
    billing_plan = coalesce(nullif(billing_plan, ''), 'individual')
where role_global is null or billing_plan is null or role_global = '';

alter table public.app_users
    alter column role_global set default 'General',
    alter column billing_plan set default 'individual';

alter table public.app_users
    drop constraint if exists app_users_role_global_check;

alter table public.app_users
    add constraint app_users_role_global_check
        check (role_global in (
            'AdminSistema',
            'AdminInstitucion',
            'AdminInstitucionSalud',
            'ProfesionalSalud',
            'Paciente',
            'Institucion',
            'General'
        ));

alter table public.app_users
    drop constraint if exists app_users_billing_plan_check;

alter table public.app_users
    add constraint app_users_billing_plan_check
        check (billing_plan in (
            'individual',
            'institution',
            'corporate',
            'b2b2c',
            'trial'
        ));

alter table public.app_users
    alter column role_global set not null,
    alter column billing_plan set not null;

create index if not exists app_users_role_global_idx
    on public.app_users (role_global);

create index if not exists app_users_billing_plan_idx
    on public.app_users (billing_plan);

-- Table: institutions --------------------------------------------------------
create table if not exists public.institutions (
    id bigserial primary key,
    name text not null,
    slug text,
    is_healthcare boolean not null default false,
    business_tier text not null default 'standard',
    metadata jsonb not null default '{}'::jsonb,
    billing_email text,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

comment on table public.institutions is 'Organizaciones que contratan o administran AURA365 (clínicas, empresas, etc.).';
comment on column public.institutions.slug is 'Identificador amigable único por institución.';
comment on column public.institutions.is_healthcare is 'True si la institución atiende pacientes (modelo clínico).';
comment on column public.institutions.business_tier is 'Plan comercial asignado a la institución.';

create unique index if not exists institutions_slug_key
    on public.institutions (lower(slug))
    where slug is not null;

create unique index if not exists institutions_name_key
    on public.institutions (lower(name));

create trigger set_institutions_updated_at
    before update on public.institutions
    for each row
    execute procedure public.set_current_timestamp_updated_at();

alter table public.institutions enable row level security;

create policy "Allow read institutions for authenticated"
    on public.institutions
    for select
    to authenticated
    using (true);

create policy "Service role manage institutions"
    on public.institutions
    for all
    to service_role
    using (true)
    with check (true);

-- Table: institution_memberships --------------------------------------------
create table if not exists public.institution_memberships (
    id bigserial primary key,
    institution_id bigint not null references public.institutions(id) on delete cascade,
    user_id bigint not null references public.app_users(id) on delete cascade,
    role_institution text not null,
    is_primary boolean not null default false,
    status text not null default 'active',
    started_at timestamptz not null default timezone('utc', now()),
    ended_at timestamptz,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now()),
    constraint institution_memberships_role_check check (
        role_institution in (
            'AdminInstitucion',
            'AdminInstitucionSalud',
            'ProfesionalSalud',
            'Paciente'
        )
    ),
    constraint institution_memberships_status_check check (
        status in ('active', 'inactive', 'suspended')
    )
);

comment on table public.institution_memberships is 'Relación usuario-institución y rol que desempeña.';
comment on column public.institution_memberships.is_primary is 'Marca la membresía principal del usuario en esa institución.';

create unique index if not exists institution_memberships_active_uniq
    on public.institution_memberships (institution_id, user_id, role_institution)
    where ended_at is null and status = 'active';

create index if not exists institution_memberships_user_idx
    on public.institution_memberships (user_id);

create index if not exists institution_memberships_institution_idx
    on public.institution_memberships (institution_id);

create trigger set_institution_memberships_updated_at
    before update on public.institution_memberships
    for each row
    execute procedure public.set_current_timestamp_updated_at();

alter table public.institution_memberships enable row level security;

create policy "Allow membership read self"
    on public.institution_memberships
    for select
    to authenticated
    using (
        exists(
            select 1
            from public.app_users au
            where au.id = public.institution_memberships.user_id
              and au.auth_user_id = auth.uid()
        )
    );

create policy "Service role manage memberships"
    on public.institution_memberships
    for all
    to service_role
    using (true)
    with check (true);

-- Table: care_relationships -------------------------------------------------
create table if not exists public.care_relationships (
    id bigserial primary key,
    professional_user_id bigint not null references public.app_users(id) on delete cascade,
    patient_user_id bigint not null references public.app_users(id) on delete cascade,
    professional_membership_id bigint references public.institution_memberships(id) on delete set null,
    patient_membership_id bigint references public.institution_memberships(id) on delete set null,
    institution_id bigint references public.institutions(id) on delete set null,
    context_type text not null,
    status text not null default 'active',
    started_at timestamptz not null default timezone('utc', now()),
    ended_at timestamptz,
    notes text,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now()),
    constraint care_relationships_context_check check (
        context_type in ('institutional', 'independent')
    ),
    constraint care_relationships_status_check check (
        status in ('active', 'inactive', 'ended')
    )
);

comment on table public.care_relationships is 'Vínculos entre profesionales y pacientes, institucionales o independientes.';

create unique index if not exists care_relationships_active_institutional_uniq
    on public.care_relationships (professional_user_id, patient_user_id, institution_id)
    where context_type = 'institutional' and status = 'active' and ended_at is null;

create unique index if not exists care_relationships_active_independent_uniq
    on public.care_relationships (professional_user_id, patient_user_id)
    where context_type = 'independent' and status = 'active' and ended_at is null;

create index if not exists care_relationships_professional_idx
    on public.care_relationships (professional_user_id);

create index if not exists care_relationships_patient_idx
    on public.care_relationships (patient_user_id);

create trigger set_care_relationships_updated_at
    before update on public.care_relationships
    for each row
    execute procedure public.set_current_timestamp_updated_at();

alter table public.care_relationships enable row level security;

create policy "Allow care read for related users"
    on public.care_relationships
    for select
    to authenticated
    using (
        exists(
            select 1
            from public.app_users au
            where au.id = public.care_relationships.professional_user_id
              and au.auth_user_id = auth.uid()
        )
        or exists(
            select 1
            from public.app_users au
            where au.id = public.care_relationships.patient_user_id
              and au.auth_user_id = auth.uid()
        )
    );

create policy "Service role manage care relationships"
    on public.care_relationships
    for all
    to service_role
    using (true)
    with check (true);

-- Table: subscriptions ------------------------------------------------------
create table if not exists public.subscriptions (
    id bigserial primary key,
    owner_type text not null,
    owner_institution_id bigint references public.institutions(id) on delete cascade,
    owner_user_id bigint references public.app_users(id) on delete cascade,
    plan_code text not null,
    billing_cycle text not null default 'monthly',
    status text not null default 'active',
    started_at timestamptz not null default timezone('utc', now()),
    ended_at timestamptz,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now()),
    constraint subscriptions_owner_type_check check (
        owner_type in ('institution', 'user')
    ),
    constraint subscriptions_status_check check (
        status in ('active', 'paused', 'canceled', 'expired')
    ),
    constraint subscriptions_owner_presence check (
        (owner_type = 'institution' and owner_institution_id is not null and owner_user_id is null)
        or (owner_type = 'user' and owner_user_id is not null)
    )
);

comment on table public.subscriptions is 'Planes contratados por usuarios o instituciones.';
comment on column public.subscriptions.plan_code is 'Código identificador del plan comercial (p.ej. free, premium, enterprise).';

create unique index if not exists subscriptions_active_unique
    on public.subscriptions (
        owner_type,
        coalesce(owner_institution_id, 0),
        coalesce(owner_user_id, 0)
    )
    where status = 'active' and ended_at is null;

create index if not exists subscriptions_owner_user_idx
    on public.subscriptions (owner_user_id)
    where owner_user_id is not null;

create index if not exists subscriptions_owner_institution_idx
    on public.subscriptions (owner_institution_id)
    where owner_institution_id is not null;

create trigger set_subscriptions_updated_at
    before update on public.subscriptions
    for each row
    execute procedure public.set_current_timestamp_updated_at();

alter table public.subscriptions enable row level security;

create policy "Allow user read own subscriptions"
    on public.subscriptions
    for select
    to authenticated
    using (
        (owner_type = 'user' and exists(
            select 1
            from public.app_users au
            where au.id = public.subscriptions.owner_user_id
              and au.auth_user_id = auth.uid()
        ))
        or
        (owner_type = 'institution' and exists(
            select 1
            from public.institution_memberships im
            join public.app_users au on au.id = im.user_id
            where im.institution_id = public.subscriptions.owner_institution_id
              and im.status = 'active'
              and au.auth_user_id = auth.uid()
        ))
    );

create policy "Service role manage subscriptions"
    on public.subscriptions
    for all
    to service_role
    using (true)
    with check (true);

-- Table: system_audit -------------------------------------------------------
create table if not exists public.system_audit (
    id bigserial primary key,
    actor_user_id bigint references public.app_users(id) on delete set null,
    action text not null,
    entity text not null,
    entity_id text,
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default timezone('utc', now())
);

comment on table public.system_audit is 'Bitácora de acciones sensibles (solo visible para AdminSistema / service_role).';

alter table public.system_audit enable row level security;

create policy "Service role manage system audit"
    on public.system_audit
    for all
    to service_role
    using (true)
    with check (true);

-- Refresh sync trigger to populate the new metadata fields ------------------
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
  role_global text := coalesce(meta ->> 'role_global', meta ->> 'role', 'General');
  billing_plan text := coalesce(meta ->> 'billing_plan', 'individual');
  is_independent boolean := false;
begin
  begin
    if raw_age is not null and raw_age ~ '^\d+$' then
      age_value := raw_age::integer;
    end if;
  exception when others then
    age_value := null;
  end;

  -- Normalize boolean flag for independent practice.
  if meta ? 'is_independent' then
    case lower(coalesce(meta ->> 'is_independent', 'false'))
      when 'true', 't', '1', 'yes', 'on' then
        is_independent := true;
      else
        is_independent := false;
    end case;
  end if;

  if tier not in ('free', 'premium') then
    tier := 'free';
  end if;

  if role_global not in (
    'AdminSistema',
    'AdminInstitucion',
    'AdminInstitucionSalud',
    'ProfesionalSalud',
    'Paciente',
    'Institucion',
    'General'
  ) then
    role_global := 'General';
  end if;

  if billing_plan not in (
    'individual',
    'institution',
    'corporate',
    'b2b2c',
    'trial'
  ) then
    billing_plan := 'individual';
  end if;

  insert into public.app_users (
    auth_user_id,
    email,
    full_name,
    age,
    phone_number,
    gender,
    tier,
    role_global,
    is_independent,
    billing_plan
  ) values (
    new.id,
    coalesce(new.email, ''),
    full_name,
    coalesce(age_value, 0),
    phone,
    gender,
    tier,
    role_global,
    is_independent,
    billing_plan
  )
  on conflict (auth_user_id) do update set
    email = excluded.email,
    full_name = excluded.full_name,
    phone_number = excluded.phone_number,
    gender = excluded.gender,
    tier = excluded.tier,
    role_global = excluded.role_global,
    is_independent = excluded.is_independent,
    billing_plan = excluded.billing_plan,
    age = case
      when excluded.age is distinct from public.app_users.age and excluded.age <> 0 then excluded.age
      else public.app_users.age
    end,
    updated_at = timezone('utc', now());

  return new;
end;
$$ language plpgsql;
