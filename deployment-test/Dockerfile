# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set the working directory in the container
WORKDIR /app

# Copy the project files
COPY pyproject.toml .
COPY requirements.txt .

# Install dependencies using uv
# We use --system to install into the system python environment since we are in a container
RUN uv pip install --system --no-cache -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Define environment variable for unbuffered output (crucial for MCP stdio)
ENV PYTHONUNBUFFERED=1

# Run server.py when the container launches
CMD ["python", "server.py"]
