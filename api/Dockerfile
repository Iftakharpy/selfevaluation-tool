FROM python:3.13-slim

# Update system packages and install prerequisites for adding MongoDB repo, then mongosh
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gnupg \
    curl \
    ca-certificates \
    && \
    # Add MongoDB GPG key & repository for mongosh
    # Using official instructions: https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-debian/
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
       gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor && \
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | \
       tee /etc/apt/sources.list.d/mongodb-org-7.0.list && \
    apt-get update && \
    # Install mongosh
    apt-get install -y --no-install-recommends mongodb-mongosh && \
    # Clean up downloaded package lists and temporary files to reduce image size
    apt-get purge -y --auto-remove gnupg curl ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

WORKDIR /root/
COPY ./requirements.txt /root/app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r app/requirements.txt

COPY ./app  /root/app

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]