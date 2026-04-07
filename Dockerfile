FROM python:3.11

# Install Go
RUN apt-get update && apt-get install -y wget tar git \
    && wget https://go.dev/dl/go1.21.6.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.21.6.linux-amd64.tar.gz

ENV PATH="/usr/local/go/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn requests pydantic

# HF Spaces uses port 7860
EXPOSE 7860

# Run server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]