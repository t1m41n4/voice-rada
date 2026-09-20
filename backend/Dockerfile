FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini entrypoint.sh ./
EXPOSE 8000
CMD ["sh", "/app/entrypoint.sh"]
