FROM python:3.11-slim

# Install Poetry
RUN pip install poetry==1.6.1
RUN poetry config virtualenvs.create false

# Set the working directory in the container
WORKDIR /code

# Copy the entire project into the container
COPY . .

# Install dependencies
RUN poetry install --no-interaction --no-ansi

EXPOSE 8080

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]
