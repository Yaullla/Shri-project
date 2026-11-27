FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SAM_BIND=0.0.0.0 PORT=8081 SAM_DB=/data/samobranka.sqlite3 SAM_ASSETS_DIR=/data/assets SAM_ACCEPT_REQUESTS=0
WORKDIR /app
RUN groupadd -g 10001 sam && useradd -u 10001 -g sam -M sam && mkdir -p /data/assets && chown -R sam:sam /data
COPY pilot_api.py miniapp.html bot.py manage_pilot.py ./
USER sam
EXPOSE 8081
CMD ["python","pilot_api.py"]
