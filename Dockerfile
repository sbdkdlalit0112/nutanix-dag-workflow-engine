FROM python:3.11-alpine
WORKDIR /app
COPY worker.py .
RUN pip install requests
ENV HOST_URL="http://host.docker.internal:8000/receive"
CMD ["python", "worker.py"]