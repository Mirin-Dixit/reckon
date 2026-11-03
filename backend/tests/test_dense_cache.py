"""Persistent cache tests with synthetic vectors; no model or network calls."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from app.ingestion.chunking import Chunk
from app.retrieval import cache as module
from app.retrieval.bm25 import BM25Index
from app.retrieval.cache import DenseIndexCache
from app.retrieval.dense import DenseIndex
from app.retrieval.hybrid import HybridIndex
from app.retrieval.ollama_embeddings import EmbeddingIdentity
from app.retrieval.resources import RAM_RESERVE_BYTES

CHUNKS = [Chunk("d_c0000", "d", 0, 0, 5, "first"),
          Chunk("d_c0001", "d", 1, 5, 11, "second")]
SETTINGS = {"snapshot_fingerprint": "a" * 64,
            "chunking": {"algorithm": "character-v1", "size": 500, "overlap": 50}}


class FakeEmbedder:
    def __init__(self):
        self.calls = 0
        self.metadata = EmbeddingIdentity("offline:model", "b" * 64, 2)

    def identity(self):
        return self.metadata

    def embed_texts(self, texts):
        self.calls += 1
        return [[float(len(t)), 1.0] for t in texts]

    def embed_query(self, text):
        return [5.0, 1.0]


def cache(path, **kwargs):
    return DenseIndexCache(path, memory_reader=lambda: 4 * 1024**3, **kwargs)


def build(store, model=None, chunks=None, **kwargs):
    return store.get_or_build(
        CHUNKS if chunks is None else chunks, model or FakeEmbedder(),
        **{**SETTINGS, **kwargs},
    )


def test_restart_reuses_persisted_vectors_and_keeps_dense_hybrid_rankings(tmp_path):
    model = FakeEmbedder()
    first = build(cache(tmp_path), model)
    restarted = FakeEmbedder()
    second = build(cache(tmp_path), restarted)
    assert not first.cache_hit and second.cache_hit
    assert model.calls == 1 and restarted.calls == 0
    assert first.vector_fingerprint == second.vector_fingerprint
    fresh = DenseIndex(CHUNKS, FakeEmbedder())
    assert fresh.search("q") == second.index.search("q")
    bm25 = BM25Index(CHUNKS)
    assert HybridIndex(bm25, fresh).search("q") == HybridIndex(
        bm25, second.index,
    ).search("q")


@pytest.mark.parametrize("change", [
    "text", "order", "offset", "id", "document", "snapshot", "chunking",
    "weights", "dimensions", "preprocessing", "context", "server", "execution",
])
def test_content_identity_invalidation(tmp_path, change):
    store = cache(tmp_path)
    model = FakeEmbedder()
    original = build(store, model)
    chunks = list(CHUNKS)
    settings = dict(SETTINGS)
    if change == "text":
        chunks[0] = replace(chunks[0], text="other")
    elif change == "order":
        chunks.reverse()
    elif change == "offset":
        chunks[0] = replace(chunks[0], start_char=2, end_char=7)
    elif change == "id":
        chunks[0] = replace(chunks[0], chunk_id="another")
    elif change == "document":
        chunks[0] = replace(chunks[0], doc_id="another")
    elif change == "snapshot":
        settings["snapshot_fingerprint"] = "c" * 64
    elif change == "chunking":
        settings["chunking"] = {**SETTINGS["chunking"], "size": 600}
    else:
        names = {"weights": "digest", "dimensions": "dimensions",
                 "preprocessing": "preprocessing", "context": "context_size",
                 "server": "server_version", "execution": "execution"}
        values = {"weights": "c" * 64, "dimensions": 3, "context": 300}
        model.metadata = replace(model.metadata, **{
            names[change]: values.get(change, "changed"),
        })
        if change == "dimensions":
            model.embed_texts = lambda texts: [[1., 2., 3.] for _ in texts]
    changed = build(store, model, chunks, **settings)
    assert changed.cache_key != original.cache_key
    assert not changed.cache_hit


@pytest.mark.parametrize("damage", ["json", "version", "manifest", "checksum",
                                    "vector", "count", "extra", "duplicate",
                                    "oversized", "unicode", "nan"])
def test_corruption_rebuilds_whole_entry(tmp_path, damage):
    store = cache(tmp_path)
    model = FakeEmbedder()
    result = build(store, model)
    path = tmp_path / f"{result.cache_key}.json"
    value = json.loads(path.read_bytes())
    if damage == "json":
        path.write_text("{", encoding="utf-8")
    elif damage == "duplicate":
        path.write_text('{"manifest":{},"manifest":{}}', encoding="utf-8")
    elif damage == "unicode":
        path.write_bytes(b"\xff")
    elif damage == "oversized":
        path.write_bytes(b" " * (store.max_entry_bytes + 1))
    else:
        if damage == "version":
            value["manifest"]["version"] = "old"
        elif damage == "manifest":
            value["manifest"]["snapshot"] = "c" * 64
        elif damage == "checksum":
            value["vector_sha256"] = "c" * 64
        elif damage == "vector":
            value["vectors"][0] = [True, 1]
        elif damage == "nan":
            value["vectors"][0][0] = float("nan")
        elif damage == "count":
            value["vectors"].pop()
        else:
            value["unexpected"] = 1
        path.write_text(json.dumps(value), encoding="utf-8")
    rebuilt = build(store, model)
    assert not rebuilt.cache_hit and model.calls == 2
    assert rebuilt.vector_fingerprint == result.vector_fingerprint
    assert build(store, model).cache_hit


def test_cache_contains_no_source_text_or_gold_fields(tmp_path):
    result = build(cache(tmp_path))
    content = (tmp_path / f"{result.cache_key}.json").read_text()
    assert "first" not in content and "second" not in content
    assert "expected_answer" not in content and "questions" not in content
    assert "text_sha256" in content
    value = json.loads(content)
    canonical = json.dumps(value["vectors"], sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(canonical.encode()).hexdigest() == result.vector_fingerprint


def test_failed_atomic_replace_preserves_old_file_and_cleans_temporary(tmp_path,
                                                                  monkeypatch):
    store = cache(tmp_path)
    result = build(store)
    path = tmp_path / f"{result.cache_key}.json"
    path.write_text("old-corrupt-entry", encoding="utf-8")

    def fail(*args):
        raise OSError("offline simulated disk failure")

    monkeypatch.setattr(module.os, "replace", fail)
    with pytest.raises(OSError):
        build(store)
    assert path.read_text() == "old-corrupt-entry"
    assert not list(tmp_path.glob(".dense-*.tmp"))


def test_bounded_entries_preserve_unrelated_files(tmp_path):
    store = cache(tmp_path, max_entries=2)
    unrelated = tmp_path / "notes.json"
    unrelated.write_text("preserve", encoding="utf-8")
    results = [build(store, snapshot_fingerprint=str(i) * 64) for i in range(3)]
    assert len(list(tmp_path.glob("*.json"))) == 3
    assert unrelated.read_text() == "preserve"
    assert not (tmp_path / f"{results[0].cache_key}.json").exists()
    assert build(store, snapshot_fingerprint="2" * 64).cache_hit


def test_total_byte_quota_and_oversized_entry(tmp_path):
    first = build(cache(tmp_path))
    size = (tmp_path / f"{first.cache_key}.json").stat().st_size
    store = cache(tmp_path, max_entry_bytes=size + 10, max_total_bytes=size + 10)
    build(store, snapshot_fingerprint="c" * 64)
    assert len(list(tmp_path.glob("*.json"))) == 1
    with pytest.raises(ValueError, match="capacity"):
        build(cache(tmp_path / "small", max_entry_bytes=512))
    assert not list((tmp_path / "small").glob("*.json"))


def test_same_process_concurrent_instances_build_once(tmp_path):
    model = FakeEmbedder()
    with ThreadPoolExecutor(max_workers=4) as workers:
        results = list(workers.map(lambda _: build(cache(tmp_path), model), range(8)))
    assert sum(not r.cache_hit for r in results) == 1
    assert model.calls == 1


def test_embedding_failure_is_not_cached(tmp_path):
    class Broken(FakeEmbedder):
        def embed_texts(self, texts):
            raise TimeoutError("offline")

    with pytest.raises(TimeoutError):
        build(cache(tmp_path), Broken())
    assert not list(tmp_path.iterdir())


def test_model_identity_changes_during_build_are_not_published(tmp_path):
    class Changed(FakeEmbedder):
        def embed_texts(self, texts):
            self.metadata = replace(self.metadata, digest="c" * 64)
            return super().embed_texts(texts)

    with pytest.raises(ValueError, match="identity changed"):
        build(cache(tmp_path), Changed())
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("kwargs", [
    {"max_entries": 0}, {"max_entries": True}, {"max_entries": 33},
    {"max_entry_bytes": 1}, {"max_total_bytes": 100},
])
def test_invalid_capacity_rejected(tmp_path, kwargs):
    with pytest.raises(ValueError):
        cache(tmp_path, **kwargs)


def test_duplicate_chunks_bad_snapshot_and_memory_rejected(tmp_path):
    model = FakeEmbedder()
    with pytest.raises(ValueError):
        build(cache(tmp_path), model, [CHUNKS[0]] * 2)
    with pytest.raises(ValueError):
        build(cache(tmp_path), model, snapshot_fingerprint="../unsafe")
    store = DenseIndexCache(tmp_path, memory_reader=lambda: RAM_RESERVE_BYTES - 1)
    with pytest.raises(ValueError, match="RAM"):
        build(store, model)
    assert model.calls == 0 and not list(tmp_path.iterdir())


def test_empty_corpus_round_trip(tmp_path):
    first = build(cache(tmp_path), chunks=[])
    second = build(cache(tmp_path), chunks=[])
    assert second.cache_hit and first.index.search("q") == []


def test_format_version_invalidates_key(tmp_path, monkeypatch):
    first = build(cache(tmp_path))
    monkeypatch.setattr(module, "CACHE_VERSION", "offline-test-next-version")
    second = build(cache(tmp_path))
    assert first.cache_key != second.cache_key and not second.cache_hit


def test_read_cannot_use_symlink_entry(tmp_path, monkeypatch):
    first = build(cache(tmp_path))
    path = tmp_path / f"{first.cache_key}.json"
    path_type = type(path)
    original = path_type.is_symlink
    monkeypatch.setattr(path_type, "is_symlink", lambda p: p == path or original(p))
    with pytest.raises(ValueError, match="Symlink"):
        build(cache(tmp_path))


def test_cache_hit_still_requires_ram_reserve(tmp_path):
    build(cache(tmp_path))
    store = DenseIndexCache(tmp_path, memory_reader=lambda: RAM_RESERVE_BYTES - 1)
    with pytest.raises(ValueError, match="RAM"):
        build(store)


def test_bad_offsets_rejected_before_embedding(tmp_path):
    model = FakeEmbedder()
    with pytest.raises(ValueError, match="offsets"):
        build(cache(tmp_path), model, [replace(CHUNKS[0], end_char=100)])
    assert model.calls == 0


def test_bad_vector_from_embedder_never_publishes(tmp_path):
    model = FakeEmbedder()
    model.embed_texts = lambda texts: [[float("inf"), 0] for _ in texts]
    with pytest.raises(ValueError):
        build(cache(tmp_path), model)
    assert not list(tmp_path.iterdir())
