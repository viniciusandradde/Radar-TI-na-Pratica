FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY collector/requirements-postgres.txt /app/collector/
RUN pip install -r /app/collector/requirements-postgres.txt
COPY collector/ /app/collector/
COPY deploy/scheduler.py /app/scheduler.py
RUN useradd --system --uid 10001 radar
USER radar
# Agendador: roda collect.py de hora em hora no minuto COLLECT_MINUTE.
# Coleta avulsa: docker compose run --rm radar-scheduler python collector/collect.py
CMD ["python", "/app/scheduler.py"]
