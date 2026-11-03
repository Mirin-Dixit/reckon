"""Bounded JSON vector cache, keyed only by corpus snapshot and embedding identity."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from app.ingestion.chunking import Chunk
from app.retrieval.dense import DenseIndex, Embedder
from app.retrieval.ollama_embeddings import EmbeddingIdentity, checked_vectors
from app.retrieval.resources import RAM_RESERVE_BYTES, available_ram_bytes

CACHE_VERSION = "ragbench.dense.v1"


class IdentifiedEmbedder(Embedder, Protocol):
    def identity(self) -> EmbeddingIdentity:
        """Return verified local weights and preprocessing identity."""
        ...


def _encoded(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_encoded(value)).hexdigest()


def _object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate cache JSON key")
        result[key] = value
    return result


@dataclass(frozen=True)
class CachedDenseIndex:
    index: DenseIndex
    cache_key: str
    vector_fingerprint: str
    cache_hit: bool


class DenseIndexCache:
    """Single-process synchronized cache with atomic cross-process publication.

    Separate processes may compute the same missing key, but never publish a
    partial file. Use a private trusted directory: hashes detect corruption,
    not malicious replacement by a writer who can recompute the checksum.
    No arbitrary Python callbacks are sandboxed. No benchmark questions load here.
    """

    _lock = threading.RLock()

    def __init__(
        self, directory: Path, *, max_entries: int = 8,
        max_entry_bytes: int = 2_097_152, max_total_bytes: int = 16_777_216,
        memory_reader: Callable[[], int] = available_ram_bytes,
    ) -> None:
        if (type(max_entries) is not int or not 1 <= max_entries <= 32
                or type(max_entry_bytes) is not int
                or not 512 <= max_entry_bytes <= 4_194_304
                or type(max_total_bytes) is not int
                or not max_entry_bytes <= max_total_bytes <= 67_108_864):
            raise ValueError("Invalid cache capacity")
        self.directory = Path(directory).resolve()
        self.max_entries = max_entries
        self.max_entry_bytes = max_entry_bytes
        self.max_total_bytes = max_total_bytes
        self._memory = memory_reader

    def get_or_build(
        self, chunks: list[Chunk], embedder: IdentifiedEmbedder, *,
        snapshot_fingerprint: str, chunking: Mapping[str, object],
    ) -> CachedDenseIndex:
        """Reuse only the exact ordered corpus snapshot; return existing DenseIndex.

        The caller supplies a documents-only snapshot hash, never a question hash
        or annotations. Full chunk identities independently protect snapshot reuse.
        Cache files contain hashes/IDs/offsets and vectors, not document text.
        """
        if not isinstance(snapshot_fingerprint, str) or not re.fullmatch(
            r"[0-9a-f]{64}", snapshot_fingerprint,
        ):
            raise ValueError("A documents snapshot SHA-256 is required")
        if len(chunks) > 256 or len({c.chunk_id for c in chunks}) != len(chunks):
            raise ValueError("Cache requires at most 256 uniquely identified chunks")
        if any(c.end_char - c.start_char != len(c.text) for c in chunks):
            raise ValueError("Chunk offsets must match the supplied source text")
        identity = embedder.identity()
        manifest = {
            "version": CACHE_VERSION, "snapshot": snapshot_fingerprint,
            "embedding": asdict(identity), "chunking": dict(chunking),
            "chunks": [dict(
                chunk_id=c.chunk_id, doc_id=c.doc_id, index=c.index,
                start_char=c.start_char, end_char=c.end_char,
                text_sha256=hashlib.sha256(c.text.encode("utf-8")).hexdigest(),
            ) for c in chunks],
        }
        key = _hash(manifest)
        with self._lock:
            self._check_memory()
            self.directory.mkdir(parents=True, exist_ok=True)
            path = self.directory / f"{key}.json"
            vectors = self._read(path, manifest, len(chunks), identity.dimensions)
            hit = vectors is not None
            if vectors is None:
                vectors = checked_vectors(
                    embedder.embed_texts([c.text for c in chunks]),
                    len(chunks), identity.dimensions,
                )
                if embedder.identity() != identity:
                    raise ValueError("Embedding identity changed during cache build")
                self._check_memory()
                body = _encoded({
                    "manifest": manifest, "vectors": vectors,
                    "vector_sha256": _hash(vectors),
                })
                if len(body) > self.max_entry_bytes:
                    raise ValueError("Dense cache entry exceeds capacity")
                self._publish(path, body)
            self._prune(path)
            return CachedDenseIndex(
                DenseIndex(list(chunks), embedder, chunk_embeddings=vectors),
                key, _hash(vectors), hit,
            )

    def _check_memory(self) -> None:
        available = self._memory()
        if type(available) is not int or available < RAM_RESERVE_BYTES:
            raise ValueError("Dense cache RAM safety reserve is unavailable")

    def _read(self, path: Path, manifest: dict, count: int, dimensions: int):
        if path.is_symlink():
            raise ValueError("Symlink cache entries are forbidden")
        try:
            with path.open("rb") as source:
                body = source.read(self.max_entry_bytes + 1)
            if len(body) > self.max_entry_bytes:
                return None
            value = json.loads(body, object_pairs_hook=_object)
            if not isinstance(value, dict) or set(value) != {
                "manifest", "vectors", "vector_sha256",
            } or _hash(value["manifest"]) != _hash(manifest):
                return None
            vectors = checked_vectors(value["vectors"], count, dimensions)
            if _hash(vectors) != value["vector_sha256"]:
                return None
            return vectors
        except FileNotFoundError:
            return None
        except (ValueError, TypeError, OverflowError, RecursionError):
            # Rebuild using the supplied snapshot, never a partial cached index.
            return None

    def _publish(self, path: Path, body: bytes) -> None:
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=self.directory, prefix=".dense-", suffix=".tmp", delete=False,
            ) as target:
                temporary = Path(target.name)
                target.write(body)
                target.flush()
                os.fsync(target.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _prune(self, current: Path) -> None:
        # Evict only owned, direct regular files. No recursive or unrelated deletes.
        entries = [p for p in self.directory.iterdir()
                   if re.fullmatch(r"[0-9a-f]{64}\.json", p.name)
                   and not p.is_symlink() and p.is_file()]
        entries.sort(key=lambda p: (p == current, p.stat().st_mtime_ns, p.name))
        size = sum(p.stat().st_size for p in entries)
        while len(entries) > self.max_entries or size > self.max_total_bytes:
            victim = entries.pop(0)
            if victim == current or victim.resolve().parent != self.directory:
                raise ValueError("Cache cannot maintain capacity safely")
            size -= victim.stat().st_size
            victim.unlink()
