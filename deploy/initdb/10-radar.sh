#!/bin/sh
# Primeira subida do volume: cria radar_app (dono do vsa_radar), aplica o schema
# como radar_app e cria radar_ro (somente leitura, para o Media Desk).
set -eu

psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  -v app_pw="$RADAR_APP_PASSWORD" -v ro_pw="$RADAR_RO_PASSWORD" <<'SQL'
create role radar_app login password :'app_pw';
create role radar_ro login password :'ro_pw';
create database vsa_radar owner radar_app;
revoke all on database vsa_radar from public;
grant connect on database vsa_radar to radar_ro;
SQL

psql -v ON_ERROR_STOP=1 -U radar_app -d vsa_radar -f /radar/schema.sql

psql -v ON_ERROR_STOP=1 -U radar_app -d vsa_radar <<'SQL'
grant usage on schema public to radar_ro;
-- O Media Desk lê só o contrato news_items v1. sources fica para conferência de origem.
-- Nada de select em todas as tabelas: leads, lead_email_log e app_users têm dado pessoal (LGPD).
grant select on news_items, sources to radar_ro;
SQL
