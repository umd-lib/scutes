# Pull base image
FROM python:3.14.6-slim

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /opt/scutes

# Copy project files
COPY src ./src
COPY pyproject.toml .

# Install dependencies
RUN apt-get update && apt-get install -y xmlsec1 libssl-dev libsasl2-dev git
RUN pip install -e .

# Commands to run migration and start the server
RUN python src/manage.py collectstatic --noinput
CMD python src/manage.py migrate && python src/manage.py runserver 0.0.0.0:15000
