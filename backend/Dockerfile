# Multi-stage build for Python backend with system dependencies
FROM python:3.11-slim as base

# Install system dependencies for PDF processing and unstructured
# These are needed for poppler (pdf2image), tesseract (OCR), libmagic (file type detection),
# and OpenCV (for unstructured_inference which uses cv2)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libmagic-dev \
    libmagic1 \
    libtesseract-dev \
    libleptonica-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install langchain-google-genai if not in requirements
RUN pip install --no-cache-dir langchain-google-genai || true

# Copy application code
COPY . .

# Create directories for data persistence
RUN mkdir -p /app/data/uploads /app/data/logs /app/chroma_db /app/data/parents_index

# Note: .env file should be mounted as volume from project root in docker-compose.yml

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health', timeout=5)" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

