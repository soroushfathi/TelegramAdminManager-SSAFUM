FROM python:latest
COPY ssafumadmin.py .
COPY main.session .
COPY requirements.txt .
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3" ]
CMD [ "ssafumadmin.py" ]