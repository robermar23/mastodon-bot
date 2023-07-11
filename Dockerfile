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
  curl \
  musl-dev \
  openssl-dev \
  cargo \
  pkgconfig \
  git \
  cython

WORKDIR /app

# Make sure we use the virtualenv:
#ENV PATH="/opt/venv/bin:$PATH"
#https://github.com/rust-lang/cargo/issues/2808
ENV CARGO_NET_GIT_FETCH_WITH_CLI=true
ENV POETRY_VERSION=1.4.0

RUN pip install --upgrade pip
RUN pip install "poetry==$POETRY_VERSION"
RUN python -m venv /venv

COPY poetry.lock pyproject.toml ./

RUN poetry export -f requirements.txt | /venv/bin/pip install -r /dev/stdin

COPY . .
RUN poetry build && /venv/bin/pip install dist/*.whl


FROM python:3.10-alpine as builder-image

WORKDIR /opt/mastodonbot
#needed by pillow just to use it
RUN apk add --no-cache zlib libjpeg openjpeg tiff libimagequant libxcb libpng libffi
#RUN apk add --no-cache zlib libjpeg libwebpmux3 libopenjp2-7 liblcms2-2 libwebpdemux2 libjpeg-turbo8
COPY --from=compiler-image /venv /venv

# Make sure we use the virtualenv:
ENV PATH="/venv/bin:$PATH"

#RUN source $HOME/.cargo/env && echo $PATH

CMD ["mastodonbotcli"]
