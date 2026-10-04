FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --system --create-home --shell /usr/sbin/nologin finzo

COPY --chown=finzo:finzo app.py schemas.py ./
COPY --chown=finzo:finzo database/ ./database/
COPY --chown=finzo:finzo dependencies/ ./dependencies/
COPY --chown=finzo:finzo repositories/ ./repositories/
COPY --chown=finzo:finzo routes/ ./routes/
COPY --chown=finzo:finzo services/ ./services/
COPY --chown=finzo:finzo static/ ./static/
COPY --chown=finzo:finzo templates/ ./templates/

USER finzo

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '8000') + '/health', timeout=3)" || exit 1

CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
