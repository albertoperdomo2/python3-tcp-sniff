FROM python:3.8
LABEL maintainer="alperga.ulpgc@gmail.com"

WORKDIR /src
COPY . /src
 
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "src/gather.py"]
# enable verbosity
CMD ["-vv"]
