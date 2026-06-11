# backbone

Clean Architecture + CQRS kernel — available in Python and Go.

| | Python | Go |
|---|---|---|
| Folder | [`backbone-python/`](./backbone-python/README.md) | [`backbone-go/`](./backbone-go/README.md) |
| Install | `pip install git+https://github.com/FreakJazz/backbone.git#subdirectory=backbone-python` | `go get github.com/freakjazz/backbone-go` |
| Example | `backbone-python/examples/clean_api_python/` | `backbone-go/examples/clean-api-go/` |

Both implementations share identical response contracts, exception codes, filter operators, and log shapes.

---

## Run examples

```bash
# Python
cd backbone-python/examples/clean_api_python
pip install flask flask-restx
python main.py          # → http://localhost:5000/docs

# Go
cd backbone-go/examples/clean-api-go
go mod tidy
go run main.go          # → http://localhost:8080/swagger/
```
