# clean_api_python — build context is this directory (self-contained: unlike
# the Go example, backbone is installed for real from GitHub via pip, not
# vendored from a sibling module in this monorepo — see requirements.txt).
#
# Build:
#   docker build -t clean-api-python examples/python/clean_api_python
FROM python:3.12-slim AS base
WORKDIR /app

# No apt-get / system packages needed: requirements.txt installs backbone
# from a plain HTTPS tarball URL (see its comment), which pip fetches and
# unpacks itself — unlike a git+https:// requirement, that needs no `git`
# binary in the image.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -u 10001 -m appuser
USER appuser

EXPOSE 5000
CMD ["python", "main.py"]
