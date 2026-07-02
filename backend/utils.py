"""Utility module for vector operations and SHA256-based embedding."""

import hashlib
import math
from typing import Optional


def text_to_vector(text: str, dim: int = 64) -> list[float]:
    """Convert text to a deterministic float vector using SHA256 hashing.

    Splits text into chunks and hashes each chunk to produce a fixed-dimension
    floating-point vector suitable for cosine similarity comparison.
    """
    if not text.strip():
        return [0.0] * dim

    # Generate enough hash bytes
    vector = [0.0] * dim
    # Use multiple hash rounds to cover all dimensions
    for i in range(math.ceil(dim / 32) + 1):
        h = hashlib.sha256(f"{text}:{i}".encode("utf-8")).digest()
        start = i * 32
        for j in range(min(32, dim - start)):
            # Convert byte to float in [-1, 1] range
            val = (h[j] - 128) / 128.0
            vector[start + j] += val

    # Normalize to unit vector
    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 0:
        vector = [v / magnitude for v in vector]

    return vector[:dim]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not vec_a or not vec_b:
        return 0.0
    dim = min(len(vec_a), len(vec_b))
    dot = sum(vec_a[i] * vec_b[i] for i in range(dim))
    mag_a = math.sqrt(sum(v * v for v in vec_a[:dim]))
    mag_b = math.sqrt(sum(v * v for v in vec_b[:dim]))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
