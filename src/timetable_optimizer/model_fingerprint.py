"""Deterministic fingerprints for persisted Stage 4 model/search inputs.

Long-running search state is valid only for the exact model that produced it.  Structural
catalogue identity alone is insufficient: changing a preference, degree scenario, future
opportunity, recognition evidence, registration observation, or temporal policy changes the
meaning of an accumulated frontier.

This module canonicalizes the immutable/data-oriented Stage 4 objects used by the solver and
hashes that representation.  It intentionally rejects unsupported Python objects rather than
falling back to ``repr()``, whose ordering/identity can be process-dependent.
"""

from __future__ import annotations

import base64
from collections.abc import Mapping, Sequence, Set
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any


class ModelFingerprintError(TypeError):
    """An object cannot be represented safely in a deterministic model fingerprint."""


def _type_name(value: object) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def canonical_model_value(value: Any) -> Any:
    """Return a JSON-compatible deterministic representation with explicit type markers."""

    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ModelFingerprintError("non-finite float cannot enter model fingerprint")
        # Distinguish floats from integers and preserve Python's round-trippable precision.
        return {"__float__": repr(value)}
    if isinstance(value, bytes):
        return {"__bytes__": base64.b64encode(value).decode("ascii")}
    if isinstance(value, Path):
        return {"__path__": value.as_posix()}
    if isinstance(value, Enum):
        return {
            "__enum__": _type_name(value),
            "value": canonical_model_value(value.value),
        }
    if is_dataclass(value) and not isinstance(value, type):
        return {
            "__dataclass__": _type_name(value),
            "fields": {
                item.name: canonical_model_value(getattr(value, item.name))
                for item in fields(value)
            },
        }
    if isinstance(value, Mapping):
        encoded_items = [
            (canonical_model_value(key), canonical_model_value(item_value))
            for key, item_value in value.items()
        ]
        encoded_items.sort(
            key=lambda item: json.dumps(
                item[0], sort_keys=True, ensure_ascii=False, separators=(",", ":")
            )
        )
        return {"__mapping__": [[key, item_value] for key, item_value in encoded_items]}
    if isinstance(value, Set) and not isinstance(value, (str, bytes, bytearray)):
        encoded = [canonical_model_value(item) for item in value]
        encoded.sort(
            key=lambda item: json.dumps(
                item, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            )
        )
        return {"__set__": encoded}
    if isinstance(value, tuple):
        return {"__tuple__": [canonical_model_value(item) for item in value]}
    if isinstance(value, list):
        return {"__list__": [canonical_model_value(item) for item in value]}
    # Other Sequence implementations can be surprising (numpy arrays, mutable custom
    # containers).  Do not silently fingerprint their repr or iteration semantics.
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        raise ModelFingerprintError(
            f"unsupported sequence type in model fingerprint: {_type_name(value)}"
        )
    raise ModelFingerprintError(
        f"unsupported object in model fingerprint: {_type_name(value)}"
    )


def model_fingerprint(value: Any, *, contract: str) -> str:
    """Hash one canonical model value under an explicit versioned semantic contract."""

    if not contract.strip():
        raise ModelFingerprintError("fingerprint contract must be nonblank")
    payload = {
        "contract": contract,
        "value": canonical_model_value(value),
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
