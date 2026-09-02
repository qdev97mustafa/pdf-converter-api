FROM python:3.10-slim

# تثبيت LibreOffice والخطوط الأساسية لدعم المستندات
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
