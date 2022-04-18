FROM python:3.6-alpine

# Install python
RUN apk add --no-cache --update alpine-sdk python3-dev libffi-dev

WORKDIR /app

# Install dependencies.
COPY blockchain /app
RUN cd /app && \
    pip install -r requirements.txt && \
    mkdir /wallets 

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["python", "server.py", "--port", "5000", "--debug", "1"]