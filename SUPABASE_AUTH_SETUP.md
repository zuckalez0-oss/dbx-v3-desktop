# Supabase Auth Setup

## Dashboard Checklist

1. Crie um projeto `DEV` no Supabase.
2. Copie:
   - `Project URL`
   - `anon public key`
3. Em `Authentication > Providers`:
   - habilite `Email`
   - desabilite cadastro público
   - desabilite `Phone`, `Anonymous` e provedores sociais nesta fase
4. Em `Authentication > URL Configuration`:
   - configure `Site URL`
   - configure `Redirect URLs`
5. Em `Authentication > Email Templates`:
   - revise `Confirm signup`
   - revise `Invite user`
   - revise `Reset password`
6. Em produção, configure SMTP próprio.

## Configuração do EXE

O desktop lê a configuração em:

`%LOCALAPPDATA%/DBX-V3 Desktop/auth/supabase_config.json`

Também aceita override por variáveis de ambiente:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `DBX_AUTH_PROFILES_TABLE`
- `DBX_AUTH_PROFILE_LOOKUP_COLUMN`
- `DBX_AUTH_REQUIRE_DBX_ACCESS_CLAIM`
- `DBX_AUTH_REQUIRE_PROFILE`
- `DBX_AUTH_DESKTOP_ACCESS_COLUMN`
- `DBX_AUTH_STATUS_COLUMN`
- `DBX_AUTH_ALLOWED_STATUSES`

Existe um exemplo em [supabase_config.example.json](C:/repos/dbx-v3-desktop/supabase_config.example.json).

## SQL Bootstrap

Execute no SQL Editor do Supabase de `DEV`:

```sql
begin;

create extension if not exists "pgcrypto";

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text,
    display_name text,
    company_id uuid null,
    status text not null default 'pending',
    desktop_access boolean not null default false,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.profiles (id, email, display_name)
    values (
        new.id,
        new.email,
        coalesce(
            new.raw_user_meta_data ->> 'display_name',
            new.raw_user_meta_data ->> 'full_name',
            split_part(coalesce(new.email, ''), '@', 1)
        )
    )
    on conflict (id) do update
    set
        email = excluded.email,
        display_name = coalesce(public.profiles.display_name, excluded.display_name),
        updated_at = timezone('utc', now());

    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;

create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_auth_user();

create or replace function public.set_profile_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = timezone('utc', now());
    return new;
end;
$$;

drop trigger if exists set_profiles_updated_at on public.profiles;

create trigger set_profiles_updated_at
before update on public.profiles
for each row execute procedure public.set_profile_updated_at();

alter table public.profiles enable row level security;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own"
on public.profiles
for select
to authenticated
using ((select auth.uid()) = id);

drop policy if exists "profiles_update_own_basic_fields" on public.profiles;
create policy "profiles_update_own_basic_fields"
on public.profiles
for update
to authenticated
using ((select auth.uid()) = id)
with check (
    (select auth.uid()) = id
    and desktop_access = (select desktop_access from public.profiles where id = auth.uid())
    and status = (select status from public.profiles where id = auth.uid())
);

commit;
```

## Liberação de Usuário

Depois do bootstrap:

1. Crie ou convide o usuário no Dashboard.
2. Defina `app_metadata.dbx_access = true`.
3. Ajuste o `profile` para:
   - `desktop_access = true`
   - `status = 'active'`
4. Valide o login no EXE.

## Fluxo Recomendado Para Novos Usuários em PROD

### Opção A. Operação manual pelo Dashboard + SQL Editor

Fluxo recomendado para os primeiros clientes:

1. Acesse `Authentication > Users`.
2. Crie ou convide o novo usuário.
3. Confirme que o email do usuário foi criado corretamente.
4. No `SQL Editor`, rode:

```sql
select id, email
from auth.users
where email = 'usuario@empresa.com';
```

5. Defina o acesso DBX no `app_metadata`:

```sql
update auth.users
set raw_app_meta_data = coalesce(raw_app_meta_data, '{}'::jsonb)
    || '{"dbx_access": true}'::jsonb
where email = 'usuario@empresa.com';
```

6. Defina o nick/nome de usuário no `user_metadata`:

```sql
update auth.users
set raw_user_meta_data = coalesce(raw_user_meta_data, '{}'::jsonb)
    || '{"username": "Matheus"}'::jsonb
where email = 'usuario@empresa.com';
```

7. Garanta que o profile esteja ativo:

```sql
insert into public.profiles (id, email, display_name, status, desktop_access)
select id, email, 'Matheus', 'active', true
from auth.users
where email = 'usuario@empresa.com'
on conflict (id) do update
set
  email = excluded.email,
  display_name = excluded.display_name,
  status = 'active',
  desktop_access = true,
  updated_at = timezone('utc', now());
```

8. Envie ao usuário:
   - email cadastrado
   - senha inicial ou convite
   - orientação de primeiro acesso

### O que controla o acesso hoje

Para a branch atual, o usuário entra no DBX quando estas regras são verdadeiras:

- login com email e senha válido
- `raw_app_meta_data.dbx_access = true`
- se existir profile:
  - `desktop_access = true`
  - `status = 'active'` ou `trial`

### O que controla o nome exibido no app

A saudação `Olá, ...` segue esta prioridade:

1. `profiles.username`
2. `profiles.nickname`
3. `profiles.nick`
4. `profiles.display_name`
5. `auth.users.raw_user_meta_data.username`
6. `auth.users.raw_user_meta_data.nickname`
7. `auth.users.raw_user_meta_data.nick`
8. `auth.users.raw_user_meta_data.display_name`
9. `auth.users.raw_user_meta_data.full_name`
10. email

### Padrão sugerido para PROD

Para simplificar o suporte:

- usar `username` como nick principal do usuário
- usar `display_name` no profile para nome amigável
- manter `dbx_access` no `app_metadata`
- manter `desktop_access` e `status` no `profiles`
