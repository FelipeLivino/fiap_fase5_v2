FROM python:3.12.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_DATA_DIR=/app/runtime
WORKDIR /app
COPY automation/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    groupadd --gid 10001 cardioia && useradd --uid 10001 --gid cardioia --no-create-home cardioia && \
    mkdir -p /app/runtime && chown cardioia:cardioia /app/runtime
COPY --chown=cardioia:cardioia . .
USER cardioia
CMD ["python", "-m", "automation.robot"]
