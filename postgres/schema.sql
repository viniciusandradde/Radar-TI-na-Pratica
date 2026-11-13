-- VSA Radar — schema para PostgreSQL próprio (substitui supabase/schema.sql).
-- Equivalente funcional das tabelas do Supabase, sem dependência de auth.users
-- nem de RLS por auth.uid(): autenticação e autorização passam para a API
-- (ADR-001). Idempotente: pode ser executado mais de uma vez.
-- Executar conectado como o dono do banco (radar_app), no banco vsa_radar.

create extension if not exists pgcrypto;

-- Substitui auth.users do Supabase: usuários do workspace editorial.
create table if not exists public.app_users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  display_name text not null default '',
  role text not null default 'editor' check (role in ('owner','admin','editor','reviewer','viewer')),
  created_at timestamptz not null default now()
);

-- Dono padrão do workspace (o coletor grava em nome dele quando VSA_OWNER_ID não é informado).
insert into public.app_users (email, display_name, role)
values ('editorial@vsa-radar.local', 'Editorial VSA', 'owner')
on conflict (email) do nothing;

create table if not exists public.news_items (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.app_users(id) on delete cascade,
  source_name text not null,
  source_url text,
  canonical_url text not null,
  title text not null,
  summary text,
  published_at timestamptz,
  category text not null default 'Mercado & Estratégia',
  status text not null default 'new' check (status in ('new','review','approved','rejected')),
  created_at timestamptz not null default now(),
  unique(owner_id, canonical_url)
);
create index if not exists news_items_owner_published_idx on public.news_items(owner_id, published_at desc);
create index if not exists news_items_owner_status_idx on public.news_items(owner_id, status);

create table if not exists public.drafts (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.app_users(id) on delete cascade,
  news_id uuid references public.news_items(id) on delete set null,
  title text not null default '',
  angle text not null default '',
  body text not null default '',
  sources text not null default '',
  status text not null default 'draft' check (status in ('draft','review','approved','published','archived')),
  scheduled_for timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists drafts_owner_updated_idx on public.drafts(owner_id, updated_at desc);

create table if not exists public.sources (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.app_users(id) on delete cascade,
  name text not null,
  homepage_url text not null,
  feed_url text,
  category text not null default 'Mercado & Estratégia',
  enabled boolean not null default true,
  created_at timestamptz not null default now(),
  unique(owner_id, homepage_url)
);

-- Novo: histórico de execuções do coletor (status real de cada coleta).
create table if not exists public.collector_runs (
  id uuid primary key default gen_random_uuid(),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null default 'running' check (status in ('running','success','partial','failed')),
  feeds_ok integer not null default 0,
  items_seen integer not null default 0,
  items_new integer not null default 0,
  items_duplicate integer not null default 0,
  sources_skipped integer not null default 0,
  errors integer not null default 0,
  details jsonb not null default '[]'::jsonb
);
create index if not exists collector_runs_started_idx on public.collector_runs(started_at desc);

-- CRM (mantido para equivalência com o schema Supabase; sem dados migrados).
create table if not exists public.leads (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.app_users(id) on delete cascade,
  name text not null default '',
  email text,
  phone text,
  company text,
  niche text not null default 'Não classificado',
  temperature text not null default 'cold' check (temperature in ('hot','warm','cold')),
  role text,
  source text,
  consent_status text not null default 'unknown' check (consent_status in ('opted_in','legitimate_interest_reviewed','unknown','opted_out')),
  consent_basis text,
  status text not null default 'new' check (status in ('new','contacted','qualified','customer','do_not_contact')),
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists leads_owner_email_unique on public.leads(owner_id, lower(email)) where email is not null and email <> '';
create index if not exists leads_owner_niche_temperature_idx on public.leads(owner_id, niche, temperature);

create table if not exists public.lead_email_log (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.app_users(id) on delete cascade,
  lead_id uuid not null references public.leads(id) on delete cascade,
  provider text not null default 'resend',
  provider_message_id text,
  recipient text not null,
  subject text not null,
  status text not null default 'sent',
  sent_at timestamptz not null default now()
);
