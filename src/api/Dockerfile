FROM python:3.9-slim

# Set the working directory
WORKDIR /src/api

# Copy requirements and install dependencies
COPY ./src/api/requirements.txt /src/api/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire 'api' folder
COPY ./src/api /src/api

# Expose the port Flask runs on
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
