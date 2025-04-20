# Use the official Python image as the base image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing pyc files and to buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# docker image version
ENV VERSION=0.2.5

# Set the working directory
WORKDIR /app

# Add a non-root user for security
RUN useradd -m appuser

# Copy requirements.txt
COPY requirements.txt /app/

# Install dependencies
RUN apt-get update && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the entire project
COPY . /app/

# Create or update db.sqlite3 permissions and collect static files
RUN touch db.sqlite3 && \
    python manage.py collectstatic --noinput && \
    chown -R appuser:appuser /app && \
    chmod -R 775 /app

# Expose the port on which the server will run
EXPOSE 8000

# Switch to non-root user
USER appuser

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--worker-class", "gevent", "--timeout", "120", "nftvault.wsgi:application"]

# Optionally, add a healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1