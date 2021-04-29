FROM ubuntu:18.04

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y python3 python3-pip python3-pillow python3-numpy nginx vim ffmpeg python3-opencv

RUN apt-get -y install libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev

RUN pip3 install setuptools==47.1.1
# && \
#   pip3 install grpcio==1.27.2 && \
#   pip3 install grpcio_tools==1.27.2

RUN apt-get -y install libmodbus-dev libmodbus5

COPY requirements /app/requirements
COPY requirements.txt /app/requirements.txt


WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app
COPY nginx.conf /etc/nginx/nginx.conf
COPY build_main /usr/share/nginx/html
RUN cp /app/lib/amd/* /usr/lib/
COPY sxd0020_bx3 /app
RUN chmod +x sxd0020_bx3

CMD ["bash", "run.sh"]

