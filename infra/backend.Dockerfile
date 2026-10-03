FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
WORKDIR /app
RUN python -m venv /opt/venv
COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY infra/bootstrap.py ./bootstrap.py
EXPOSE 8000
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "bootstrap:application"]
