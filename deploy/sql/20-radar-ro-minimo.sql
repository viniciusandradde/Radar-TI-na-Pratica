-- Restringe o papel radar_ro (Media Desk) às tabelas do contrato em volumes já criados.
-- Idempotente. Rodar como superusuário no banco vsa_radar:
--   psql -v ON_ERROR_STOP=1 -U postgres -d vsa_radar -f deploy/sql/20-radar-ro-minimo.sql
begin;
alter default privileges for role radar_app in schema public revoke select on tables from radar_ro;
revoke select on all tables in schema public from radar_ro;
grant select on news_items, sources to radar_ro;
commit;
