FROM python:3.11-slim
WORKDIR /app
COPY requirement.txt /app/requirement.txt
RUN pip install --no-cache-dir -r /app/requirement.txt
COPY . /app
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]