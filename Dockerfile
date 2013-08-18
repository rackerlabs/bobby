FROM ubuntu:12.04

# The build process isn't a real tty
ENV DEBIAN_FRONTEND noninteractive

# Use the Rackspace mirrors, they're usually much faster
RUN echo "deb http://mirror.rackspace.com/ubuntu/ precise main restricted universe" > /etc/apt/sources.list
RUN echo "deb http://mirror.rackspace.com/ubuntu/ precise-updates main restricted universe" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y python python-dev python-pip make

ADD . /opt/bobby
RUN cd /opt/bobby; pip install -r requirements.txt

# Must pass tests to build a container
RUN cd /opt/bobby; make test

# Expose the bobby port and set a default command
EXPOSE 9876
CMD /bin/bash -c "cd /opt/bobby; twistd -l /var/log/bobby/logs -n bobby"
