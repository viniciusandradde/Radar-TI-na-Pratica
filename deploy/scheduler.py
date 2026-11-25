"""Roda collector/collect.py de hora em hora, no minuto COLLECT_MINUTE (padrão 15).

Substitui o timer systemd da estação. Uma coleta que falha não derruba o agendador;
o resultado de cada uma fica em collector_runs e no log do contêiner.
"""
import os, subprocess, sys, time
from datetime import datetime, timedelta

MINUTE = int(os.environ.get("COLLECT_MINUTE", "15"))
TIMEOUT = 50 * 60  # uma coleta nunca encosta na seguinte


def next_run(now: datetime) -> datetime:
    target = now.replace(minute=MINUTE, second=0, microsecond=0)
    return target if target > now else target + timedelta(hours=1)


def main():
    print(f"[scheduler] coleta de hora em hora aos :{MINUTE:02d}", flush=True)
    while True:
        when = next_run(datetime.now())
        print(f"[scheduler] próxima coleta {when:%Y-%m-%d %H:%M}", flush=True)
        time.sleep(max(0, (when - datetime.now()).total_seconds()))
        try:
            rc = subprocess.run([sys.executable, "/app/collector/collect.py"], timeout=TIMEOUT).returncode
            print(f"[scheduler] coleta terminou com código {rc}", flush=True)
        except subprocess.TimeoutExpired:
            print("[scheduler] coleta passou de 50 min e foi interrompida", flush=True)


if __name__ == "__main__":
    main()
