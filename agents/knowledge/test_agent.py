"""Offline RAG regression tests. Fake vectors make ranking/cache behavior deterministic."""
import json
from pathlib import Path
import sqlite3

import pytest
from rag import Chunk, NOT_FOUND, RagEngine, chunk_document, normalize


class FakeBackend:
    cache_key = "fake:3:v1"

    def __init__(self):
        self.calls = []
        self.generated = []
        self.reply = "The frontend uses React. [1]"

    def embed(self, texts, task):
        self.calls.append((task, list(texts)))
        vectors = []
        for text in texts:
            text = text.lower()
            # Deliberately map synonyms without requiring matching keywords.
            if any(word in text for word in ("frontend", "react", "interface", "giao diện")):
                vectors.append([1, 0, 0])
            elif any(word in text for word in ("database", "storage", "postgres")):
                vectors.append([0, 1, 0])
            else:
                vectors.append([0, 0, 1])
        return vectors

    def generate(self, question, sources):
        self.generated.append((question, sources))
        return self.reply


@pytest.fixture
def corpus(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "ui.md").write_text("# Client\nThe frontend uses React.\n", encoding="utf-8")
    (data / "db.txt").write_text("# Persistence\nThe database uses Postgres.\n", encoding="utf-8")
    backend = FakeBackend()
    engine = RagEngine(data, tmp_path / "cache" / "vectors.sqlite3", backend=backend, top_k=2)
    return engine, backend, data


def test_chunk_bounds_overlap_and_exact_source_lines():
    text = "# Header\n" + "abcdefghij " * 90
    chunks = chunk_document(text, "guide.md", size=200, overlap=40)
    assert len(chunks) > 1
    assert all(0 < len(c.text) <= 200 for c in chunks)
    assert chunks[0].text[-30:] in chunks[1].text
    assert all(c.heading == "Header" for c in chunks)
    assert len({c.id for c in chunks}) == len(chunks)
    assert chunks == chunk_document(text, "guide.md", size=200, overlap=40)
    assert chunks[0].start_line == 1


def test_heading_boundaries_unicode_and_blank_content():
    text = "# First\nNội dung tiếng Việt.\n\n## Second\nReact UI.\n"
    chunks = chunk_document(text, "nested/test.md")
    assert len(chunks) == 2
    assert chunks[1].start_line == 4
    assert chunks[1].end_line == 5
    assert chunks[1].heading == "Second"
    assert chunk_document(" \n", "empty.txt") == []
    with pytest.raises(ValueError):
        chunk_document("text", "bad.txt", 100, 50)


def test_semantic_synonyms_and_vietnamese(corpus):
    engine, backend, _ = corpus
    for query in ("Which interface is used?", "Giao diện dùng gì?"):
        result = engine.retrieve(query)
        assert result["status"] == "ok"
        assert result["sources"][0]["source"] == "ui.md"
        assert result["sources"][0]["score"] == 1
        assert len(result["sources"]) == 1
    assert {task for task, _ in backend.calls} == {"RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"}


def test_cache_reused_across_engine_instances(corpus):
    engine, backend, data = corpus
    engine.retrieve("interface")
    assert len([x for x in backend.calls if x[0] == "RETRIEVAL_DOCUMENT"]) == 1
    new_engine = RagEngine(data, engine.cache_path, backend=backend)
    new_engine.retrieve("interface")
    assert len([x for x in backend.calls if x[0] == "RETRIEVAL_DOCUMENT"]) == 1


def test_changed_and_removed_files_invalidate_cache(corpus):
    engine, backend, data = corpus
    engine.retrieve("interface")
    (data / "ui.md").write_text("# New\nDatabase storage only.", encoding="utf-8")
    assert engine.retrieve("interface")["status"] == "not_found"
    assert len([x for x in backend.calls if x[0] == "RETRIEVAL_DOCUMENT"]) == 2
    (data / "ui.md").unlink()
    (data / "db.txt").unlink()
    assert engine.retrieve("interface")["sources"] == []
    with sqlite3.connect(engine.cache_path) as db:
        assert db.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0] == 0


def test_model_change_invalidates_cache(corpus):
    engine, backend, _ = corpus
    engine.retrieve("interface")
    backend.cache_key = "fake:model-v2"
    engine.retrieve("interface")
    assert len([x for x in backend.calls if x[0] == "RETRIEVAL_DOCUMENT"]) == 2


def test_answer_uses_retrieved_evidence_and_real_citations(corpus):
    engine, backend, _ = corpus
    result = engine.answer("interface")
    assert "[1] ui.md, lines 1-2" in result
    assert "db.txt" not in result
    assert backend.generated[0][1][0]["text"] == "# Client\nThe frontend uses React."


@pytest.mark.parametrize("reply", ["Invented source. [99]", "No source provided", "", NOT_FOUND])
def test_reject_unfounded_or_invalid_citations(corpus, reply):
    engine, backend, _ = corpus
    backend.reply = reply
    assert engine.answer("interface") == NOT_FOUND


def test_no_match_does_not_generate(corpus):
    engine, backend, _ = corpus
    assert engine.answer("astronomy") == NOT_FOUND
    assert backend.generated == []


def test_hidden_and_unsupported_files_are_not_indexed(corpus):
    engine, _, data = corpus
    (data / ".secret.txt").write_text("React secret")
    (data / "ignored.json").write_text('{"frontend": "secret"}')
    hidden = data / ".hidden"
    hidden.mkdir()
    (hidden / "secret.md").write_text("React secret")
    assert {c.source for c in engine._load_chunks()} == {"ui.md", "db.txt"}


def test_reject_invalid_query_and_vectors(corpus):
    engine, _, _ = corpus
    for value in ("", " ", "x" * 8001, None):
        with pytest.raises(ValueError):
            engine.retrieve(value)
    for value in ([], [0, 0], [float("nan")], [float("inf")]):
        with pytest.raises(ValueError):
            normalize(value)


def test_dimension_mismatch_is_error_not_false_match(corpus):
    engine, backend, _ = corpus
    engine.retrieve("interface")
    backend.embed = lambda texts, task: [[1, 0] for _ in texts]
    with pytest.raises(ValueError, match="dimension"):
        engine.retrieve("interface")


def test_file_size_is_bounded(corpus):
    engine, _, data = corpus
    (data / "large.txt").write_bytes(b"x" * 2_000_001)
    with pytest.raises(ValueError, match="2 MB"):
        engine.retrieve("interface")