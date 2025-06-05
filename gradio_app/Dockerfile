# Use an official Python runtime as a parent image
FROM ghcr.io/astral-sh/uv:python3.13-alpine

RUN apk add --no-cache gcc cmake python3-dev g++ make musl-dev linux-headers apache-arrow-dev libffi-dev libvpx-dev opus opus-dev libsrtp-dev py3-cffi py3-pip py3-setuptools

# Create and set the working directory
WORKDIR /app

# Copy your requirements file into the image
COPY . .

RUN uv export > requirements.txt
RUN pip install cffi
RUN pip install -r requirements.txt

# Remove apk cache
RUN rm -rf /var/cache/apk/*

# Expose the default port for the application
EXPOSE 8501

# Set environment variables for production
ENV PYTHONPATH=/app
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8501

# Set the command to run your FastAPI app using uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host=0.0.0.0", "--port=8501"]
