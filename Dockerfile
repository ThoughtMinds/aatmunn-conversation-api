FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt . 

RUN pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY static ./static

EXPOSE 8000

CMD ["uvicorn", "api.main:server", "--host", "0.0.0.0", "--port", "8000", "--reload"]