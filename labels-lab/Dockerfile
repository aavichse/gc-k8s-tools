# Use an official Python runtime as a parent image
FROM python:3.9-slim

WORKDIR /app

# Copy the current directory contents into the container at /app
COPY templates/ /app/templates
COPY requirements.txt /app
COPY gc-labels-lab.py /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define the command to run the Flask app, using environment variables for PORT
ENTRYPOINT ["python", "gc-labels-lab.py"]
