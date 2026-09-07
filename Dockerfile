FROM python:3.14-slim
WORKDIR /OpsDesk
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /OpsDesk
EXPOSE 5000 
CMD ["python", "run.py"]