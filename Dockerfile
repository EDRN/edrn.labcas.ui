# Image for LabCAS UI
# ===================

# I'd use Alpine, but I don't yet know atk
FROM debian:latest

# Install dependencies
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        python-pip \
        python-dev \
        curl \
        libldap2-dev \
        libsasl2-dev \
        swig \
        libssl-dev \
        gcc \
    && pip install --upgrade pip setuptools

# Doing this first for caching reasons, apparently
# (??? see https://runnable.com/docker/python/dockerize-your-pyramid-application)
COPY ./requirements.txt /app/

# Let's get going
WORKDIR /app/
RUN pip install -r requirements.txt && mkdir src docs
COPY MANIFEST.in README.rst setup.py app.py /app/
COPY src src
COPY docs docs
RUN python setup.py install

# And let's get running
ENTRYPOINT ["python"]
CMD ["app.py"]
