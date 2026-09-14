-- Pulse cloud sync — Supabase schema.
-- Already applied to the shared project (rlaeklherxdfrlbduqde, also used by staff-scheduler's bb_* objects).
-- To set up a fresh project, run this once in the SQL Editor.
--
-- One vault per sync key. Tables are locked (RLS on, no policies, no grants); the app reaches them
-- only through the key-checked SECURITY DEFINER functions below. Keys are stored as SHA-256 hashes.

create table public.pulse_vaults (
  id uuid primary key default gen_random_uuid(),
  key_hash text not null unique,
  data jsonb not null,
  version bigint not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
-- short-lived pairing codes so a phone can join without typing the 64-char key
create table public.pulse_pair_codes (
  code_hash text primary key,
  vault_id uuid not null references public.pulse_vaults(id) on delete cascade,
  sync_key text not null,
  expires_at timestamptz not null
);
create index pulse_pair_codes_vault_idx on public.pulse_pair_codes(vault_id);
create table public.pulse_pair_fails (
  id bigint generated always as identity primary key,
  at timestamptz not null default now()
);
create index pulse_pair_fails_at_idx on public.pulse_pair_fails(at);

alter table public.pulse_vaults enable row level security;
alter table public.pulse_pair_codes enable row level security;
alter table public.pulse_pair_fails enable row level security;
revoke all on public.pulse_vaults, public.pulse_pair_codes, public.pulse_pair_fails from anon, authenticated;

create or replace function public.pulse__hash(p text) returns text
language sql immutable set search_path = pg_catalog, public
as $$ select encode(sha256(convert_to(p, 'UTF8')), 'hex') $$;

-- coalesce: a missing "entries" key would otherwise make this NULL, and "if not NULL" does not reject
create or replace function public.pulse__valid(p jsonb) returns boolean
language sql immutable set search_path = pg_catalog, public
as $$ select coalesce(p is not null and jsonb_typeof(p) = 'object' and jsonb_typeof(p->'entries') = 'array' and octet_length(p::text) <= 5000000, false) $$;

-- data format version stored in the document as "fv" (missing = 1)
create or replace function public.pulse__fv(p jsonb) returns int
language sql immutable set search_path = pg_catalog, public
as $$ select case when (p->>'fv') ~ '^[0-9]{1,4}$' then (p->>'fv')::int else 1 end $$;

create or replace function public.pulse_create(p_data jsonb) returns jsonb
language plpgsql security definer set search_path = public
as $$
declare k text; v bigint;
begin
  if not pulse__valid(p_data) then return jsonb_build_object('error', 'bad_data'); end if;
  k := replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '');
  insert into pulse_vaults (key_hash, data) values (pulse__hash(k), p_data) returning version into v;
  return jsonb_build_object('key', k, 'version', v);
end $$;

create or replace function public.pulse_version(p_key text) returns jsonb
language sql stable security definer set search_path = public
as $$
  select coalesce(
    (select jsonb_build_object('version', version) from pulse_vaults where key_hash = pulse__hash(p_key)),
    jsonb_build_object('error', 'bad_key'))
$$;

create or replace function public.pulse_pull(p_key text) returns jsonb
language sql stable security definer set search_path = public
as $$
  select coalesce(
    (select jsonb_build_object('data', data, 'version', version) from pulse_vaults where key_hash = pulse__hash(p_key)),
    jsonb_build_object('error', 'bad_key'))
$$;

-- optimistic concurrency: a stale p_base gets the current data back so the client can merge and retry
create or replace function public.pulse_push(p_key text, p_data jsonb, p_base bigint) returns jsonb
language plpgsql security definer set search_path = public
as $$
declare r pulse_vaults;
begin
  select * into r from pulse_vaults where key_hash = pulse__hash(p_key) for update;
  if not found then return jsonb_build_object('error', 'bad_key'); end if;
  if not pulse__valid(p_data) then return jsonb_build_object('error', 'bad_data'); end if;
  -- an outdated page (older data format) must not overwrite data written by a newer one:
  -- it would silently drop fields it does not know about
  if pulse__fv(r.data) > pulse__fv(p_data) then
    return jsonb_build_object('error', 'outdated', 'version', r.version);
  end if;
  if r.version <> p_base then
    return jsonb_build_object('error', 'conflict', 'data', r.data, 'version', r.version);
  end if;
  update pulse_vaults set data = p_data, version = version + 1, updated_at = now()
   where id = r.id returning version into r.version;
  return jsonb_build_object('version', r.version);
end $$;

-- 8-character code, valid 10 minutes, one active code per vault
create or replace function public.pulse_pair_start(p_key text) returns jsonb
language plpgsql security definer set search_path = public
as $$
declare
  vid uuid;
  alphabet constant text := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  b bytea := uuid_send(gen_random_uuid());
  code text := '';
  i int;
  exp timestamptz := now() + interval '10 minutes';
begin
  select id into vid from pulse_vaults where key_hash = pulse__hash(p_key);
  if vid is null then return jsonb_build_object('error', 'bad_key'); end if;
  delete from pulse_pair_codes where expires_at < now() or vault_id = vid;
  -- uuid bytes 6 and 8 carry version/variant bits; the rest are random
  foreach i in array array[0, 1, 2, 3, 4, 5, 7, 9] loop
    code := code || substr(alphabet, get_byte(b, i) % 32 + 1, 1);
  end loop;
  insert into pulse_pair_codes (code_hash, vault_id, sync_key, expires_at) values (pulse__hash(code), vid, p_key, exp);
  return jsonb_build_object('code', code, 'expires_at', exp);
end $$;

-- single use; after 20 wrong codes in 10 minutes (from anyone) pairing is paused
create or replace function public.pulse_pair_claim(p_code text) returns jsonb
language plpgsql security definer set search_path = public
as $$
declare
  c text := upper(regexp_replace(coalesce(p_code, ''), '[^A-Za-z0-9]', '', 'g'));
  r pulse_pair_codes;
begin
  delete from pulse_pair_fails where at < now() - interval '1 day';
  if (select count(*) from pulse_pair_fails where at > now() - interval '10 minutes') >= 20 then
    return jsonb_build_object('error', 'locked');
  end if;
  delete from pulse_pair_codes where code_hash = pulse__hash(c) and expires_at > now() returning * into r;
  if r.code_hash is null then
    insert into pulse_pair_fails default values;
    return jsonb_build_object('error', 'bad_code');
  end if;
  return jsonb_build_object('key', r.sync_key);
end $$;

revoke all on function public.pulse__hash(text), public.pulse__valid(jsonb), public.pulse__fv(jsonb) from public, anon, authenticated;
revoke all on function public.pulse_create(jsonb), public.pulse_version(text), public.pulse_pull(text),
  public.pulse_push(text, jsonb, bigint), public.pulse_pair_start(text), public.pulse_pair_claim(text) from public;
grant execute on function public.pulse_create(jsonb), public.pulse_version(text), public.pulse_pull(text),
  public.pulse_push(text, jsonb, bigint), public.pulse_pair_start(text), public.pulse_pair_claim(text) to anon, authenticated;
