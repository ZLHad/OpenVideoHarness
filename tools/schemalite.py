"""A very small JSON Schema validator, for the tools that have no third-party dependency (stdlib only; Python 3.9).

It takes the keywords tools/schemas/*.schema.json are written with: type (one, or a list), required, properties, items,
enum, anyOf, and an internal $ref ("#", "#/$defs/x"), plus the ones that say nothing about a value ($schema, $id, title,
description, $defs). It reads them as draft 2020-12 does: a required or properties on what is not an object says nothing
about it, a true or false is not a number, 1.0 is an integer, an enum compares by value (1 is 1.0, not true).
tools/ci.sh checks each schema against the real jsonschema, and the two against good and bad fixtures
(tools/schemas/fixtures/): a keyword other than these is refused, so they cannot disagree on one this does not read.

problems(schema, value) → ["$.a[2]: …"], empty when the value fits; keywords(schema) → the keywords it does not read.
"""
import json
from pathlib import Path

READS = {"type", "required", "properties", "items", "enum", "anyOf", "$ref"}
SAYS_NOTHING = {"$schema", "$id", "title", "description", "$defs"}
MAX_REF_DEPTH = 64   # a $ref that goes round without reading any of the value


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _is_type(value, name):
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "string":
        return isinstance(value, str)
    if name == "null":
        return value is None
    if name == "boolean":
        return isinstance(value, bool)
    if isinstance(value, bool):   # a true or false is no number
        return False
    if name == "number":
        return isinstance(value, (int, float))
    if name == "integer":
        return isinstance(value, int) or (isinstance(value, float) and value.is_integer())
    raise ValueError(f"unknown type {name!r}")


def _same(a, b):
    """JSON equality: 1 is 1.0, a true is not 1, in lists and objects too."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    return a == b


def _resolve(root, ref):
    if ref == "#":
        return root
    if not ref.startswith("#/"):
        raise ValueError(f"$ref {ref!r}: only an internal one is read")
    node = root
    for part in ref[2:].split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    return node


def _kind(value):
    for name in ("null", "boolean", "string", "array", "object"):
        if _is_type(value, name):
            return name
    return "number"


def _check(schema, value, root, at, out, depth):
    if schema is True:
        return
    if schema is False:
        out.append(f"{at}: nothing fits here")
        return
    if "$ref" in schema:
        if depth >= MAX_REF_DEPTH:
            raise ValueError(f"{at}: $ref {schema['$ref']!r} goes round without reading the value")
        _check(_resolve(root, schema["$ref"]), value, root, at, out, depth + 1)
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(value, n) for n in names):
            out.append(f"{at}: {_kind(value)}, not {' or '.join(names)}")
    if "enum" in schema and not any(_same(value, x) for x in schema["enum"]):
        out.append(f"{at}: {json.dumps(value, ensure_ascii=False)[:60]} is none of {json.dumps(schema['enum'], ensure_ascii=False)[:80]}")
    if isinstance(value, dict):
        for k in schema.get("required", []):
            if k not in value:
                out.append(f"{at}: no {k}")
        for k, sub in schema.get("properties", {}).items():
            if k in value:
                _check(sub, value[k], root, f"{at}.{k}", out, 0)
    if isinstance(value, list) and "items" in schema:
        for i, x in enumerate(value):
            _check(schema["items"], x, root, f"{at}[{i}]", out, 0)
    if "anyOf" in schema:
        tried = []
        for sub in schema["anyOf"]:
            one = []
            _check(sub, value, root, at, one, depth)
            if not one:
                tried = None
                break
            tried.append(one)
        if tried is not None:   # what the nearest shape lacks says more than "none of them"
            out.append(f"{at}: fits none of its {len(tried)} shapes; the nearest: " + "; ".join(min(tried, key=len)[:3]))


def problems(schema, value):
    """What keeps the value from fitting the schema, a line each: [] when it fits."""
    out = []
    _check(schema, value, schema, "$", out, 0)
    return out


def undeclared(schema, value):
    """The keys of the value's objects that the schema's properties do not name, where it names any ("$.a[0].b"). A schema allows
    them: a client takes fields it does not know; tools/test_contract.py asks for each to be written down, so its loss is seen."""
    out = []

    def walk(s, v, at, depth):
        if not isinstance(s, dict):
            return
        if "$ref" in s and depth < MAX_REF_DEPTH:
            walk(_resolve(schema, s["$ref"]), v, at, depth + 1)
        for sub in s.get("anyOf", []):
            one = []
            _check(sub, v, schema, at, one, 0)
            if not one:
                walk(sub, v, at, depth)
                break
        if isinstance(v, dict) and "properties" in s:
            out.extend(f"{at}.{k}" for k in v if k not in s["properties"])
            for k, sub in s["properties"].items():
                if k in v:
                    walk(sub, v[k], f"{at}.{k}", 0)
        if isinstance(v, list) and "items" in s:
            for i, x in enumerate(v):
                walk(s["items"], x, f"{at}[{i}]", 0)
    walk(schema, value, "$", 0)
    return out


def keywords(schema):
    """The keywords this schema uses that this validator does not read: {keyword, …}. It walks every subschema."""
    bad = set()

    def walk(s):
        if not isinstance(s, dict):
            return
        bad.update(set(s) - READS - SAYS_NOTHING)
        for sub in s.get("properties", {}).values():
            walk(sub)
        for sub in s.get("$defs", {}).values():
            walk(sub)
        for sub in s.get("anyOf", []):
            walk(sub)
        if isinstance(s.get("items"), list):   # draft 2020-12 has no list-form items (prefixItems): this reads one schema, not a list
            bad.add("items (a list)")
        walk(s.get("items"))
    walk(schema)
    return bad
