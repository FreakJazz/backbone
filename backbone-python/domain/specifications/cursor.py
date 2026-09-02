"""
Cursor (keyset) pagination — opaque tokens identifying a position in a
result set.

The alternative to LIMIT/OFFSET that doesn't degrade as the offset grows:
instead of "skip 50,000 rows, then return 20", a keyset query says "give me
the 20 rows right after this one", which Postgres can satisfy with a direct
index seek regardless of how deep into the result set that is.

Same wire format as backbone-go's EncodeCursor/DecodeCursor (base64 of a
`{"v": ..., "id": ...}` JSON payload) — contracts match backbone Python and
Go exactly, same as everywhere else in this library.
"""
import base64
import json
from typing import Any, Tuple


def encode_cursor(sort_value: Any, id_: str) -> str:
    """Returns an opaque, URL-safe token identifying a position in a
    keyset-paginated result set.

    sort_value is whatever the query's sort field held on the last row of
    the page just returned; id_ is that row's unique identifier — required
    because the sort field alone can tie (two products at the same price);
    without a tiebreaker, a tie could make keyset pagination skip or repeat
    rows across pages.

    Treat the token as a black box: its shape isn't part of the contract,
    and it is not signed or encrypted — a client can decode it, so don't
    put anything in sort_value that shouldn't be visible to them (it's
    already visible in the row that produced it, so this is normally a
    non-issue).
    """
    raw = json.dumps({"v": sort_value, "id": id_}, default=str).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def decode_cursor(token: str) -> Tuple[Any, str]:
    """Parses a token produced by encode_cursor. Returns (sort_value, id).

    sort_value comes back typed the way json.loads decodes it (a number,
    string, bool, or None) — the caller, which knows the sort field's real
    column type, is responsible for converting it before binding it as a
    query parameter. That mirrors how FilterParser already converts raw
    query-string text to a concrete type before building a Specification:
    type coercion for a dynamic field belongs to the caller who knows the
    schema, not to this generic module.

    Raises ValueError if the token is malformed or missing an id.
    """
    try:
        padding = "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(token + padding)
        payload = json.loads(raw)
    except Exception as exc:
        raise ValueError(f"invalid cursor: {exc}") from exc

    id_ = payload.get("id") if isinstance(payload, dict) else None
    if not id_:
        raise ValueError("invalid cursor: missing id")
    return payload.get("v"), id_
