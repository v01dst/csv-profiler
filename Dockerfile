FROM python:3.14-slim
WORKDIR /app
COPY csv_profiler ./csv_profiler
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python3", "-m", "csv_profiler"]
