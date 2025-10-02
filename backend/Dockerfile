FROM python:3.13 AS build
WORKDIR /app
COPY src /app/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM build AS final
WORKDIR /app

CMD ["uvicorn" , "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

