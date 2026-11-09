# Compila o MinIO (edicao comunitaria, AGPL) a partir do codigo-fonte oficial.
# Tag usada: a ultima que ainda traz o Console Web completo.
FROM golang:1.24-bookworm AS build
ARG MINIO_TAG=RELEASE.2025-04-22T22-12-26Z
RUN git clone --depth 1 --branch ${MINIO_TAG} https://github.com/minio/minio.git /src
WORKDIR /src
RUN CGO_ENABLED=0 go build -trimpath -o /out/minio .

FROM alpine:3.20
RUN apk add --no-cache ca-certificates
COPY --from=build /out/minio /usr/bin/minio
EXPOSE 9000 9001
ENTRYPOINT ["/usr/bin/minio"]
