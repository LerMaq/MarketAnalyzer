FROM python:3.13-slim

# Скопировать из папки проекта в папку контейнера
COPY .. .


RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]