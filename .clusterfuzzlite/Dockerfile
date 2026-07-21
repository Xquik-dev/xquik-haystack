FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:bb1b8ebd512e29bc955d2ef4de4b141b38809249cc66ff2fd2947dfcb6a9b012

COPY src $SRC/xquik-haystack/src
COPY .clusterfuzzlite $SRC/xquik-haystack/.clusterfuzzlite

WORKDIR $SRC/xquik-haystack

COPY .clusterfuzzlite/build.sh $SRC/
