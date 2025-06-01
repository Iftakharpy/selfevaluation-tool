FROM python:3.13-slim

# Update system packages to reduce vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean


WORKDIR /root/
COPY ./requirements.txt /root/app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r app/requirements.txt

COPY ./app  /root/app

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]
