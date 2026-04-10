# Use official lightweight Python image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit app
COPY app.py .

# Streamlit exposes port 8503
EXPOSE 8503

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8503", "--server.address=0.0.0.0"]
