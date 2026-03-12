FROM python:3.11-slim
WORKDIR /backend
# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# Copy your code
COPY . .
# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]