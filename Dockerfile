FROM tensorflow/tensorflow
FROM pytorch/pytorch

COPY requirements.txt . 

RUN pip install -r requirements.txt 

COPY mainfile.py /app/mainfile.py

CMD ["python3", "/app/mainfile.py"]
