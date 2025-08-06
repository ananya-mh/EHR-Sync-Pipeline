# Start from official Python image
FROM python:3.12-slim

# Set working directory in the container
WORKDIR /app

# Copy requirements file into the container
COPY requirements.txt .

# Create a virtual environment inside the container
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# Copy the application code into the container
COPY . .

# Activate the venv and set PATH
ENV PATH="/app/venv/bin:$PATH"

# Command to run the application
CMD ["python", "app/main.py"]