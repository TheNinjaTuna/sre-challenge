FROM python:3.11-slim

WORKDIR /app

# install dependencies
COPY /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY app/ .

# create directory for SQLite DB
RUN mkdir -p /data

ENV SQLITE_DB_PATH=/data/database.db

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "warning", "application:app"]