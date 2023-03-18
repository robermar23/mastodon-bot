FROM python:3.10-alpine as compiler-image

# install extra packages for openai and pillow python install
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
  libffi-dev \
  curl

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

RUN python -m venv /opt/venv

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements/requirements.txt .

RUN pip install --upgrade pip
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

# runs setup.py
RUN python -m pip install .

FROM python:3.10-alpine as builder-image

#needed by pillow just to use it
RUN apk add --no-cache zlib libjpeg openjpeg tiff libimagequant libxcb libpng libffi
#RUN apk add --no-cache zlib libjpeg libwebpmux3 libopenjp2-7 liblcms2-2 libwebpdemux2 libjpeg-turbo8
COPY --from=compiler-image /opt/venv /opt/venv

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$HOME/.cargo/env:$PATH"

RUN source $HOME/.cargo/env && echo $PATH

CMD ["mastodonbotcli"]
