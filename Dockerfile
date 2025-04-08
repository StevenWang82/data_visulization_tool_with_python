# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 8050 available to the world outside this container
EXPOSE 8050

# Define environment variable (optional, Dash default is 8050)
# ENV PORT=8050

# Run app.py when the container launches
CMD ["python", "app.py"]
