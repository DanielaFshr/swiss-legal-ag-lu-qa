FROM python:3.11-slim
WORKDIR /app
COPY src/ ./src/
COPY docs/evidence/ ./docs/evidence/
CMD ["python", "src/reproduce.py"]
