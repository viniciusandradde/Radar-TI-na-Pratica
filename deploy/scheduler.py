"""Agendador do Radar.

- Coleta: collector/collect.py de hora em hora, no minuto COLLECT_MINUTE (padrão 15).
- Resumo diário: collector/digest.py às DIGEST_HOUR:00 (padrão 7), só se DIGEST_ENABLED=1.

Substitui o timer systemd da estação. Uma tarefa que falha não derruba o agendador;
o resultado fica em collector_runs e no log do contêiner. Horários em TZ (America/Sao_Paulo).
"""
import os, subprocess, sys, time
from datetime import datetime, timedelta

MINUTE = int(os.environ.get("COLLECT_MINUTE", "15"))
DIGEST_ON = os.environ.get("DIGEST_ENABLED") == "1"
DIGEST_HOUR = int(os.environ.get("DIGEST_HOUR", "7"))
TIMEOUT = 50 * 60  # uma tarefa nunca encosta na seguinte


def next_collect(now: datetime) -> datetime:
    target = now.replace(minute=MINUTE, second=0, microsecond=0)
    return target if target > now else target + timedelta(hours=1)


def next_digest(now: datetime) -> datetime:
    target = now.replace(hour=DIGEST_HOUR, minute=0, second=0, microsecond=0)
    return target if target > now else target + timedelta(days=1)


def run(name: str, script: str) -> None:
    try:
        rc = subprocess.run([sys.executable, script], timeout=TIMEOUT).returncode
        print(f"[scheduler] {name} terminou com código {rc}", flush=True)
    except subprocess.TimeoutExpired:
        print(f"[scheduler] {name} passou de 50 min e foi interrompido", flush=True)


def main():
    print(f"[scheduler] coleta de hora em hora aos :{MINUTE:02d}; resumo diário "
          + (f"às {DIGEST_HOUR:02d}:00" if DIGEST_ON else "desligado (DIGEST_ENABLED != 1)"), flush=True)
    while True:
        now = datetime.now()
        jobs = [(next_collect(now), "coleta", "/app/collector/collect.py")]
        if DIGEST_ON:
            jobs.append((next_digest(now), "resumo diário", "/app/collector/digest.py"))
        when, name, script = min(jobs)
        print(f"[scheduler] próxima tarefa: {name} em {when:%Y-%m-%d %H:%M}", flush=True)
        time.sleep(max(0, (when - datetime.now()).total_seconds()))
        run(name, script)


if __name__ == "__main__":
    main()
