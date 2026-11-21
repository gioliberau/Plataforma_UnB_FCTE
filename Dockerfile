FROM python:3.12-slim

WORKDIR /bmeta

RUN pip install --no-cache-dir bottle pdfplumber

COPY . /bmeta

EXPOSE 8080

CMD ["python3", "route.py"]
