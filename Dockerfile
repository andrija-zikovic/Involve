# Base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables
ENV DB_HOST your_database_host
ENV DB_USER your_database_user
ENV DB_PASSWORD your_database_password
ENV DB_NAME your_database_name

# Expose the application port
EXPOSE 8000

# Run the application
CMD ["python", "app.py"]