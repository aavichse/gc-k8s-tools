FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the application code
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "nwsim.py"]