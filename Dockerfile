# Start from the official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies required for Poetry
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Ensure poetry's bin directory is on PATH
ENV PATH="/root/.local/bin:$PATH"
# Disable virtualenv creation, so dependencies install globally
ENV POETRY_VIRTUALENVS_CREATE=false

# Copy poetry files to the container
COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
RUN poetry install --no-dev

# Copy the bot module into the container
COPY . .

# Run the bot module
CMD ["python", "-m", "bot"]
