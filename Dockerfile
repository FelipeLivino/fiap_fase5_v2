FROM python:3.12.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_DATA_DIR=/app/runtime
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    groupadd --gid 10001 cardioia && useradd --uid 10001 --gid cardioia --no-create-home cardioia && \
    mkdir -p /app/runtime && chown cardioia:cardioia /app/runtime
COPY --chown=cardioia:cardioia . .
USER cardioia
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "60", "--access-logfile", "-", "app:create_app()"]
