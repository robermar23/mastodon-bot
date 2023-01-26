FROM python:3.10-alpine as base

# install extra packages for openai python install
RUN apk update && apk add --no-cache \
                          python3-dev \
                          py3-setuptools \
                          gcc \
                          libc-dev \
                          tiff-dev \
                          jpeg-dev \
                          openjpeg-dev \
                          zlib-dev \
                          freetype-dev \
                          lcms2-dev \
                          libwebp-dev \
                          tcl-dev \
                          tk-dev \
                          harfbuzz-dev \
                          fribidi-dev \
                          libimagequant-dev \
                          libxcb-dev \
                          libpng-dev \
                          libffi-dev
WORKDIR /app

COPY requirements/requirements.txt ./

RUN pip install --upgrade pip
RUN python -m pip install --no-cache-dir -r requirements.txt

FROM base

COPY . .

# runs setup.py
RUN python -m pip install .

CMD ["bash"]
