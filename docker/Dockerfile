# Build image
FROM quay.io/fedora/fedora:44 AS builder

ARG BUILD_DEPENDENCIES="binutils glibc-common glibc-langpack-en file-devel file gcc g++ make patch glibc-devel \
    libffi-devel \
    libpq-devel \
    libxml2-devel \
    mariadb-connector-c-devel \
    openldap-devel \
    python3-devel \
    python3-pip \
    python3-cffi \
    xmlsec1-devel \
    yarn"

# ENV LC_ALL=en_US.UTF-8 \
#     LANG=en_US.UTF-8 \
#     LANGUAGE=en_US.UTF-8
ENV FLASK_APP=/build/powerdnsadmin/__init__.py

# Get dependencies
RUN dnf update -y \
    && dnf install -y ${BUILD_DEPENDENCIES}

WORKDIR /build

COPY ./requirements.txt /build/requirements.txt

# Get application dependencies
RUN python3 -m pip install -r requirements.txt

# Add sources
COPY . /build

# Prepare assets
RUN yarn install --pure-lockfile --production && \
    yarn cache clean && \
    sed -i -r -e "s|'rcssmin',\s?'cssrewrite'|'rcssmin'|g" /build/powerdnsadmin/assets.py && \
    flask assets build

RUN mv /build/powerdnsadmin/static /tmp/static && \
    mkdir /build/powerdnsadmin/static && \
    cp -r /tmp/static/generated /build/powerdnsadmin/static && \
    cp -r /tmp/static/assets /build/powerdnsadmin/static && \
    cp -r /tmp/static/img /build/powerdnsadmin/static && \
    find /tmp/static/node_modules -name 'webfonts' -exec cp -r {} /build/powerdnsadmin/static \; && \
    find /tmp/static/node_modules -name 'fonts' -exec cp -r {} /build/powerdnsadmin/static \; && \
    find /tmp/static/node_modules/icheck/skins/square -name '*.png' -exec cp {} /build/powerdnsadmin/static/generated \;

RUN { \
      echo "from flask_assets import Environment"; \
      echo "assets = Environment()"; \
      echo "assets.register('js_login', 'generated/login.js')"; \
      echo "assets.register('js_validation', 'generated/validation.js')"; \
      echo "assets.register('css_login', 'generated/login.css')"; \
      echo "assets.register('js_main', 'generated/main.js')"; \
      echo "assets.register('css_main', 'generated/main.css')"; \
    } > /build/powerdnsadmin/assets.py

# Move application
RUN mkdir -p /app && \
    cp -r /build/migrations/ /build/powerdnsadmin/ /build/run.py /app && \
    mkdir -p /app/configs && \
    cp -r /build/configs/docker_config.py /app/configs

# Distribution Image
FROM quay.io/fedora/fedora:44 AS runtime

ENV FLASK_APP=/app/powerdnsadmin/__init__.py \
    USER=pda

RUN dnf update -y && \
    dnf install -y python3 python3-redis mariadb-connector-c libpq xmlsec1 xmlsec1-openssl tzdata && \
    groupadd --system ${USER} && \
    adduser --system -g ${USER} ${USER} && \
    mkdir /data && \
    chown ${USER}:${USER} /data && \
    dnf clean all && \
    rm -rf /var/cache/dnf/*

COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/lib/python3.14/site-packages /usr/lib/python3.14/site-packages
COPY --from=builder /usr/lib64/python3.14/site-packages /usr/lib64/python3.14/site-packages
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/lib64/python3.14/site-packages /usr/local/lib64/python3.14/site-packages
COPY --from=builder --chown=root:${USER} /app /app/
COPY ./docker/entrypoint.sh /usr/bin/

WORKDIR /app

RUN chown ${USER}:${USER} ./configs /app && \
    cat ./powerdnsadmin/default_config.py ./configs/docker_config.py > ./powerdnsadmin/docker_config.py

EXPOSE 8080/tcp
USER ${USER}
HEALTHCHECK --interval=5s --timeout=5s --start-period=20s --retries=5 CMD wget --output-document=- --quiet --tries=1 http://127.0.0.1${SCRIPT_NAME:-/}
ENTRYPOINT ["entrypoint.sh"]
CMD ["gunicorn","powerdnsadmin:create_app()"]
