FROM python:3.11-slim-buster

WORKDIR /app

# Install required system dependencies and MySQL client in a single step
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libmariadb-dev \
    pkg-config \
    python3 \
    python3-pip \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Ensure Python is properly linked
RUN ln -s /usr/bin/python3 /usr/bin/python

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure manage.py is executable
RUN chmod +x manage.py

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
