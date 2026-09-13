-- 班表 · Supabase cloud sync
-- Paste this whole file into your Supabase project's SQL Editor and click Run.
-- Running it again is safe.
--
-- How access works
--   * Nobody can read the table directly (row level security is on, no policies).
--   * The app only talks to the functions below.
--   * Owner key (32 hex): full read/write. Only the owner's own devices hold it.
--   * Staff key (24 hex): shared with employees. With it, a phone can only
--       - list names/avatars (to pick who you are), and
--       - after the server checks that person's PIN, read a trimmed copy
--         (no other people's PINs, pay rates, phone numbers, leave reasons,
--          no punch-code secret, no owner passcode), and
--       - clock in/out (the server stamps the time and checks the punch code / location),
--         request leave, and change their own photo.
--   * 8 wrong PINs lock that person for 15 minutes.

create table if not exists public.bb_stores (
  id         uuid primary key default gen_random_uuid(),
  boss_key   text not null unique,
  staff_key  text not null unique,
  data       jsonb not null,
  version    bigint not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.bb_pin_fails (
  store_id uuid not null references public.bb_stores(id) on delete cascade,
  staff_id text not null,
  fails    int not null default 0,
  last_at  timestamptz not null default now(),
  primary key (store_id, staff_id)
);

alter table public.bb_stores enable row level security;
alter table public.bb_pin_fails enable row level security;
revoke all on public.bb_stores, public.bb_pin_fails from public, anon, authenticated;

/* ---------- internal helpers (not callable from the app) ---------- */

create or replace function public.bb__hex(n int) returns text
language sql volatile set search_path = public as $$
  select substr(replace(gen_random_uuid()::text || gen_random_uuid()::text, '-', ''), 1, n)
$$;

-- Same algorithm as punchCodeFor() in index.html (FNV-1a, 32-bit)
create or replace function public.bb__punch_code(p_secret text, p_step bigint) returns text
language plpgsql immutable set search_path = public as $$
declare
  s text := coalesce(nullif(p_secret, ''), 'BB') || '|' || p_step::text;
  h bigint := 2166136261;
  i int;
begin
  for i in 1..length(s) loop
    h := h # ascii(substr(s, i, 1))::bigint;
    h := (h * 16777619) % 4294967296;
  end loop;
  if h >= 2147483648 then h := h - 4294967296; end if;
  return lpad((abs(h) % 1000000)::text, 6, '0');
end $$;

-- The copy an employee's phone is allowed to see
create or replace function public.bb__redact(p_data jsonb, p_staff text) returns jsonb
language sql stable set search_path = public as $$
  select p_data || jsonb_build_object(
    'settings', coalesce(p_data->'settings', '{}'::jsonb) - 'storeSecret' - 'bossPin',
    'staff', coalesce((
      select jsonb_agg(
        case when e->>'id' = p_staff then e || '{"pin":""}'::jsonb
        else jsonb_build_object(
          'id', e->'id', 'n', e->'n', 'roles', e->'roles', 'photo', e->'photo',
          'active', e->'active', 'pay', e->'pay', 'avail', e->'avail', 'maxH', e->'maxH',
          'restDay', e->'restDay', 'rate', 0, 'pin', '', 'phone', '', 'note', '', 'hired', '')
        end order by o)
      from jsonb_array_elements(coalesce(p_data->'staff', '[]'::jsonb)) with ordinality x(e, o)), '[]'::jsonb),
    'timeoff', coalesce((
      select jsonb_agg(case when e->>'staffId' = p_staff then e else e || '{"reason":""}'::jsonb end order by o)
      from jsonb_array_elements(coalesce(p_data->'timeoff', '[]'::jsonb)) with ordinality x(e, o)), '[]'::jsonb),
    'seenNotif', '{}'::jsonb)
$$;

-- Returns null when the PIN is right, otherwise an error code
create or replace function public.bb__check_pin(p_store_id uuid, p_data jsonb, p_staff text, p_pin text) returns text
language plpgsql volatile set search_path = public as $$
declare
  f bb_pin_fails;
  real_pin text;
  is_active boolean;
begin
  select coalesce(e->>'pin', ''), coalesce((e->>'active')::boolean, true) into real_pin, is_active
    from jsonb_array_elements(coalesce(p_data->'staff', '[]'::jsonb)) e
   where e->>'id' = p_staff limit 1;
  if real_pin is null then return 'no_staff'; end if;
  if not is_active then return 'inactive'; end if;
  if real_pin = '' then return 'no_pin'; end if;

  select * into f from bb_pin_fails where store_id = p_store_id and staff_id = p_staff;
  if found and f.fails >= 8 and f.last_at > now() - interval '15 minutes' then return 'locked'; end if;

  if p_pin is null or p_pin <> real_pin then
    insert into bb_pin_fails (store_id, staff_id, fails, last_at) values (p_store_id, p_staff, 1, now())
    on conflict (store_id, staff_id) do update
      set fails = case when bb_pin_fails.last_at < now() - interval '15 minutes' then 1 else bb_pin_fails.fails + 1 end,
          last_at = now();
    return 'bad_pin';
  end if;

  delete from bb_pin_fails where store_id = p_store_id and staff_id = p_staff;
  return null;
end $$;

/* ---------- functions the app calls ---------- */

-- Upload this device's data as a new store; returns the owner key and staff key
create or replace function public.bb_create(p_data jsonb) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare r bb_stores;
begin
  if p_data is null or jsonb_typeof(p_data) <> 'object' or not (p_data ? 'staff') or not (p_data ? 'settings') then
    return jsonb_build_object('error', 'bad_data');
  end if;
  if octet_length(p_data::text) > 8000000 then return jsonb_build_object('error', 'too_big'); end if;
  insert into bb_stores (boss_key, staff_key, data) values (bb__hex(32), bb__hex(24), p_data) returning * into r;
  return jsonb_build_object('boss_key', r.boss_key, 'staff_key', r.staff_key, 'version', r.version);
end $$;

-- Cheap "has anything changed?" check, works with either key
create or replace function public.bb_version(p_key text) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(
    (select jsonb_build_object('version', version, 'role', case when boss_key = p_key then 'boss' else 'staff' end)
       from bb_stores where boss_key = p_key or staff_key = p_key limit 1),
    jsonb_build_object('error', 'bad_key'))
$$;

create or replace function public.bb_boss_pull(p_key text) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(
    (select jsonb_build_object('data', data, 'version', version, 'staff_key', staff_key) from bb_stores where boss_key = p_key),
    jsonb_build_object('error', 'bad_key'))
$$;

-- Save the owner's full data. p_base must be the version this device last saw;
-- if someone else saved in between, returns error "conflict" with the newer data to merge.
create or replace function public.bb_boss_push(p_key text, p_data jsonb, p_base bigint) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare r bb_stores;
begin
  select * into r from bb_stores where boss_key = p_key for update;
  if not found then return jsonb_build_object('error', 'bad_key'); end if;
  if p_data is null or jsonb_typeof(p_data) <> 'object' or not (p_data ? 'staff') or not (p_data ? 'settings') then
    return jsonb_build_object('error', 'bad_data');
  end if;
  if octet_length(p_data::text) > 8000000 then return jsonb_build_object('error', 'too_big'); end if;
  if r.version <> p_base then
    return jsonb_build_object('error', 'conflict', 'data', r.data, 'version', r.version);
  end if;
  update bb_stores set data = p_data, version = version + 1, updated_at = now()
   where id = r.id returning version into r.version;
  return jsonb_build_object('version', r.version);
end $$;

-- If the staff join code leaks, make a new one (old one stops working)
create or replace function public.bb_boss_rotate_staff_key(p_key text) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare k text;
begin
  update bb_stores set staff_key = bb__hex(24) where boss_key = p_key returning staff_key into k;
  if k is null then return jsonb_build_object('error', 'bad_key'); end if;
  return jsonb_build_object('staff_key', k);
end $$;

-- Names and avatars only, for the "who are you?" screen
create or replace function public.bb_staff_roster(p_key text) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(
    (select jsonb_build_object('version', version, 'data',
        bb__redact(data, null) || jsonb_build_object('shifts', '[]'::jsonb, 'punches', '[]'::jsonb,
                                                     'timeoff', '[]'::jsonb, 'tips', '{}'::jsonb))
       from bb_stores where staff_key = p_key),
    jsonb_build_object('error', 'bad_key'))
$$;

create or replace function public.bb_staff_pull(p_key text, p_staff text, p_pin text) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare r bb_stores; e text;
begin
  select * into r from bb_stores where staff_key = p_key;
  if not found then return jsonb_build_object('error', 'bad_key'); end if;
  e := bb__check_pin(r.id, r.data, p_staff, p_pin);
  if e is not null then return jsonb_build_object('error', e); end if;
  return jsonb_build_object('version', r.version, 'data', bb__redact(r.data, p_staff));
end $$;

-- Employee actions. p_op: punch_in | punch_out | leave | photo
create or replace function public.bb_staff_write(p_key text, p_staff text, p_pin text, p_op text, p_rec jsonb, p_code text)
returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare
  r bb_stores; e text; d jsonb; st jsonb; rec jsonb;
  tz text; lnow timestamp; v_date text; v_yday text; v_time text;
  win int; step bigint; idx int; code text; sh jsonb;
  dist float8; lat1 float8; lng1 float8; lat2 float8; lng2 float8;
begin
  select * into r from bb_stores where staff_key = p_key for update;
  if not found then return jsonb_build_object('error', 'bad_key'); end if;
  e := bb__check_pin(r.id, r.data, p_staff, p_pin);
  if e is not null then return jsonb_build_object('error', e); end if;
  p_rec := coalesce(p_rec, '{}'::jsonb);

  d := r.data;
  st := coalesce(d->'settings', '{}'::jsonb);
  tz := coalesce(nullif(st->>'tz', ''), 'UTC');
  begin
    lnow := now() at time zone tz;
  exception when others then
    lnow := now() at time zone 'UTC';
  end;
  v_date := to_char(lnow, 'YYYY-MM-DD');
  v_yday := to_char(lnow - interval '1 day', 'YYYY-MM-DD');
  v_time := to_char(lnow, 'HH24:MI');

  if p_op in ('punch_in', 'punch_out') then
    -- rotating store code (the app asks for it in both "code" and "location" modes)
    if coalesce(st->>'punchMode', 'free') in ('code', 'geo') then
      win := greatest(20, coalesce(nullif(st->>'codeWindow', '')::int, 60));
      step := floor(extract(epoch from now()) / win)::bigint;
      code := regexp_replace(coalesce(p_code, ''), '[^0-9]', '', 'g');
      if length(code) <> 6 or code not in (bb__punch_code(st->>'storeSecret', step),
                                           bb__punch_code(st->>'storeSecret', step - 1)) then
        return jsonb_build_object('error', 'bad_code');
      end if;
    end if;
    -- store location
    if coalesce(st->>'punchMode', 'free') = 'geo' and (st->'geo'->>'lat') is not null then
      if (p_rec->'loc'->>'lat') is null then return jsonb_build_object('error', 'need_loc'); end if;
      lat1 := (st->'geo'->>'lat')::float8; lng1 := (st->'geo'->>'lng')::float8;
      lat2 := (p_rec->'loc'->>'lat')::float8; lng2 := (p_rec->'loc'->>'lng')::float8;
      dist := 2 * 6371000 * asin(sqrt(
        power(sin(radians(lat2 - lat1) / 2), 2) +
        cos(radians(lat1)) * cos(radians(lat2)) * power(sin(radians(lng2 - lng1) / 2), 2)));
      if dist > coalesce((st->'geo'->>'radius')::float8, 150)
                + least(greatest(coalesce((p_rec->'loc'->>'acc')::float8, 0), 0), 100) then
        return jsonb_build_object('error', 'too_far', 'dist', round(dist));
      end if;
    end if;
  end if;

  if p_op = 'punch_in' then
    if exists (select 1 from jsonb_array_elements(coalesce(d->'punches', '[]'::jsonb)) p
                where p->>'staffId' = p_staff and p->>'date' = v_date) then
      return jsonb_build_object('error', 'already_in');
    end if;
    select s into sh from jsonb_array_elements(coalesce(d->'shifts', '[]'::jsonb)) s
     where s->>'staffId' = p_staff and s->>'date' = v_date
     order by (s->>'id' = p_rec->>'shiftId') desc, s->>'start' limit 1;
    if sh is null then return jsonb_build_object('error', 'no_shift'); end if;
    rec := jsonb_build_object('id', bb__hex(8), 'shiftId', sh->'id', 'staffId', p_staff, 'date', v_date,
                              'in', v_time, 'out', null, 'brk', coalesce(sh->'brk', '0'::jsonb),
                              'via', coalesce(p_rec->'via', '"free"'::jsonb));
    d := jsonb_set(d, '{punches}', coalesce(d->'punches', '[]'::jsonb) || jsonb_build_array(rec));

  elsif p_op = 'punch_out' then
    select o - 1 into idx
      from jsonb_array_elements(coalesce(d->'punches', '[]'::jsonb)) with ordinality x(p, o)
     where p->>'staffId' = p_staff and p->>'date' in (v_date, v_yday) and (p->>'out') is null
     order by p->>'date' desc limit 1;
    if idx is null then return jsonb_build_object('error', 'not_in'); end if;
    d := jsonb_set(d, array['punches', idx::text, 'out'], to_jsonb(v_time));
    d := jsonb_set(d, array['punches', idx::text, 'outVia'], coalesce(p_rec->'via', '"free"'::jsonb));

  elsif p_op = 'leave' then
    begin
      perform (p_rec->>'from')::date, (p_rec->>'to')::date;
    exception when others then
      return jsonb_build_object('error', 'bad_data');
    end;
    if (p_rec->>'to')::date < (p_rec->>'from')::date then return jsonb_build_object('error', 'bad_data'); end if;
    rec := jsonb_build_object('id', bb__hex(8), 'staffId', p_staff,
                              'from', (p_rec->>'from')::date::text, 'to', (p_rec->>'to')::date::text,
                              'type', left(coalesce(p_rec->>'type', 'personal'), 20),
                              'reason', left(coalesce(p_rec->>'reason', ''), 500),
                              'status', 'pending', 'at', v_date);
    d := jsonb_set(d, '{timeoff}', coalesce(d->'timeoff', '[]'::jsonb) || jsonb_build_array(rec));

  elsif p_op = 'photo' then
    if jsonb_typeof(p_rec->'photo') is distinct from 'null' and (
         jsonb_typeof(p_rec->'photo') is distinct from 'string'
         or left(p_rec->>'photo', 11) <> 'data:image/'
         or length(p_rec->>'photo') > 300000) then
      return jsonb_build_object('error', 'bad_data');
    end if;
    select o - 1 into idx from jsonb_array_elements(d->'staff') with ordinality x(s, o) where s->>'id' = p_staff;
    d := jsonb_set(d, array['staff', idx::text, 'photo'], coalesce(p_rec->'photo', 'null'::jsonb));

  else
    return jsonb_build_object('error', 'bad_op');
  end if;

  update bb_stores set data = d, version = version + 1, updated_at = now()
   where id = r.id returning version into r.version;
  return jsonb_build_object('version', r.version, 'data', bb__redact(d, p_staff), 'time', v_time, 'date', v_date);
end $$;

/* ---------- permissions ---------- */

revoke all on function public.bb__hex(int) from public, anon, authenticated;
revoke all on function public.bb__punch_code(text, bigint) from public, anon, authenticated;
revoke all on function public.bb__redact(jsonb, text) from public, anon, authenticated;
revoke all on function public.bb__check_pin(uuid, jsonb, text, text) from public, anon, authenticated;

grant execute on function public.bb_create(jsonb) to anon, authenticated;
grant execute on function public.bb_version(text) to anon, authenticated;
grant execute on function public.bb_boss_pull(text) to anon, authenticated;
grant execute on function public.bb_boss_push(text, jsonb, bigint) to anon, authenticated;
grant execute on function public.bb_boss_rotate_staff_key(text) to anon, authenticated;
grant execute on function public.bb_staff_roster(text) to anon, authenticated;
grant execute on function public.bb_staff_pull(text, text, text) to anon, authenticated;
grant execute on function public.bb_staff_write(text, text, text, text, jsonb, text) to anon, authenticated;
