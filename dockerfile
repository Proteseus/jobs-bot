# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Copy the .env file into the container
# COPY .env .env

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Run bot.py when the container launches
CMD ["python", "main.py"]
