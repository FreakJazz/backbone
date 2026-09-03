# clean-api-go — multi-stage build.
#
# Build context MUST be the REPOSITORY ROOT, not this directory, because
# go.mod resolves backbone-go through a local `replace` directive:
#   replace github.com/FreakJazz/backbone/backbone-go => ../../../backbone-go
# backbone-go hasn't cut a tagged release yet, so this example vendors it
# from the sibling module in this monorepo instead of a real module-proxy
# fetch — the builder stage needs both directories copied in before
# `go mod download` can resolve that path.
#
# Build (from repo root):
#   docker build -f examples/go/clean-api-go/Dockerfile -t clean-api-go .
# docker-compose.yml at examples/ already sets context/dockerfile correctly.

FROM golang:1.25-alpine AS builder
WORKDIR /workspace

# Copy the two modules the replace directive needs, dependency manifests
# first so `go mod download` layer-caches independently of source changes.
COPY backbone-go/go.mod backbone-go/go.sum ./backbone-go/
COPY examples/go/clean-api-go/go.mod examples/go/clean-api-go/go.sum ./examples/go/clean-api-go/
WORKDIR /workspace/examples/go/clean-api-go
RUN go mod download

WORKDIR /workspace
COPY backbone-go ./backbone-go
COPY examples/go/clean-api-go ./examples/go/clean-api-go

WORKDIR /workspace/examples/go/clean-api-go
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/clean-api-go .

FROM alpine:3.20
RUN apk add --no-cache ca-certificates && adduser -D -u 10001 appuser
COPY --from=builder /out/clean-api-go /usr/local/bin/clean-api-go
USER appuser
EXPOSE 8005
ENTRYPOINT ["clean-api-go"]
