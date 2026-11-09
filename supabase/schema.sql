-- VSA Radar: execute no SQL Editor do projeto Supabase.
-- O frontend usa somente a anon/publishable key + sessão Auth.
-- O service_role existe apenas como secret do GitHub Actions/collector.

create extension if not exists pgcrypto;

create table if not exists public.news_items (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
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
  owner_id uuid not null references auth.users(id) on delete cascade,
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
  owner_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  homepage_url text not null,
  feed_url text,
  category text not null default 'Mercado & Estratégia',
  enabled boolean not null default true,
  created_at timestamptz not null default now(),
  unique(owner_id, homepage_url)
);

alter table public.news_items enable row level security;
alter table public.drafts enable row level security;
alter table public.sources enable row level security;

drop policy if exists "owner manages news" on public.news_items;
create policy "owner manages news" on public.news_items for all to authenticated using (auth.uid() = owner_id) with check (auth.uid() = owner_id);
drop policy if exists "owner manages drafts" on public.drafts;
create policy "owner manages drafts" on public.drafts for all to authenticated using (auth.uid() = owner_id) with check (auth.uid() = owner_id);
drop policy if exists "owner manages sources" on public.sources;
create policy "owner manages sources" on public.sources for all to authenticated using (auth.uid() = owner_id) with check (auth.uid() = owner_id);

-- O collector faz upsert usando service_role no ambiente GitHub Actions.
-- Configure Auth > Users e copie o UUID do usuário editor para o secret VSA_OWNER_ID.
