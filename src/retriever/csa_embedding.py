"""Persistent semantic embedding index for CSA MetaOps and framework APIs."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Optional


DEFAULT_MODEL = "BAAI/bge-large-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class CSAEmbeddingError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_summary(source: Any, limit: int = 2400) -> str:
    if isinstance(source, str):
        return source[:limit]
    if not isinstance(source, dict):
        return ""
    return "\n".join(
        part for part in [
            str(source.get("file", "")),
            str(source.get("code", ""))[:limit],
        ] if part
    )


def api_embedding_text(record: dict[str, Any]) -> str:
    return "\n".join(
        part for part in [
            f"kind: {record.get('kind', '')}",
            f"name: {record.get('qualified_name') or record.get('name', '')}",
            f"signature: {record.get('signature', '')}",
            f"description: {record.get('comment', '')}",
            "includes: " + ", ".join(record.get("required_includes", [])),
            _source_summary(record.get("source") or record.get("definition")),
        ] if part and not part.endswith(": ")
    )


def build_api_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for record in [*data.get("apis", []), *data.get("types", [])]:
        document = api_embedding_text(record)
        if not document.strip():
            continue
        records.append({
            "id": record.get("id") or record.get("qualified_name") or record.get("name"),
            "document": document,
            "payload": record,
        })
    return records


def metaop_embedding_text(checker: dict[str, Any], logic: dict[str, Any]) -> str:
    frontend_by_id = {item["id"]: item["name"] for item in checker["frontends"]}
    behavior = [
        f"{key}: {'; '.join(values)}"
        for key, values in logic.get("behavior", {}).items()
        if values
    ]
    return "\n".join(part for part in [
        f"checker: {checker['implementation_class']}",
        f"summary: {checker['summary']}",
        "frontends: " + ", ".join(
            frontend_by_id[item] for item in logic["applies_to_frontends"]),
        "callbacks: " + ", ".join(logic["callback_context"]),
        f"kind: {logic['kind']}",
        f"logic: {logic['meta_op']}",
        *behavior,
    ] if part)


def build_metaop_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for checker in data["checkers"]:
        frontend_by_id = {item["id"]: item for item in checker["frontends"]}
        for logic in checker["logic_units"]:
            records.append({
                "id": logic["id"],
                "document": metaop_embedding_text(checker, logic),
                "payload": {
                    "checker_id": checker["id"],
                    "implementation_class": checker["implementation_class"],
                    "summary": checker["summary"],
                    "analysis_mode": checker["analysis_mode"],
                    "frontends": [frontend_by_id[item] for item in logic["applies_to_frontends"]],
                    "callbacks": logic["callback_context"],
                    "kind": logic["kind"],
                    "meta_op": logic["meta_op"],
                    "behavior": logic["behavior"],
                    "meta_impl": logic["meta_impl"],
                    "source_spans": logic["source_spans"],
                    "api_refs": logic["api_refs"],
                    "depends_on": logic["depends_on"],
                },
            })
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise CSAEmbeddingError("CSA MetaOp IDs must be unique")
    return records


def _default_encoder(model_name_or_path: str):
    local_hf_home = Path(__file__).resolve().parents[1] / "retriever/embedding_model/huggingface"
    if local_hf_home.exists():
        os.environ.setdefault("HF_HOME", str(local_hf_home))
        # The weights are already in that cache. Without this, every load on an
        # air-gapped host burns ~20 minutes on HEAD requests that cannot
        # succeed, once per rule. Set HF_HUB_OFFLINE=0 to force online.
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise CSAEmbeddingError(
            "sentence-transformers is required for CSA embedding retrieval; "
            "install project embedding dependencies first"
        ) from exc
    return SentenceTransformer(model_name_or_path, device="cpu")


class CSAEmbeddingRetriever:
    """Build and query normalized BGE vectors with fingerprinted disk caching."""

    def __init__(
        self,
        metaop_path,
        api_path,
        cache_dir,
        model_name_or_path=DEFAULT_MODEL,
        encoder_factory: Optional[Callable[[str], Any]] = None,
        batch_size=32,
    ):
        self.metaop_path = Path(metaop_path).resolve()
        self.api_path = Path(api_path).resolve()
        self.cache_dir = Path(cache_dir).resolve()
        self.model_name_or_path = str(model_name_or_path)
        self.encoder_factory = encoder_factory or _default_encoder
        self.batch_size = max(1, int(batch_size))
        self._encoder = None
        self._meta_records = None
        self._api_records = None
        self._meta_embeddings = None
        self._api_embeddings = None
        self._last_cache_hit = None

    @property
    def manifest_path(self):
        return self.cache_dir / "manifest.json"

    def _fingerprint(self):
        return {
            "format_version": 1,
            "model": self.model_name_or_path,
            "metaop_sha256": _sha256(self.metaop_path),
            "api_sha256": _sha256(self.api_path),
        }

    def _encoder_instance(self):
        if self._encoder is None:
            self._encoder = self.encoder_factory(self.model_name_or_path)
        return self._encoder

    def _cache_valid(self):
        required = [
            self.manifest_path,
            self.cache_dir / "metaop_records.json",
            self.cache_dir / "api_records.json",
            self.cache_dir / "metaop_embeddings.npy",
            self.cache_dir / "api_embeddings.npy",
        ]
        if not all(path.exists() for path in required):
            return False
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8")) == self._fingerprint()
        except (OSError, json.JSONDecodeError):
            return False

    def build(self, force=False):
        try:
            import numpy as np
        except ImportError as exc:
            raise CSAEmbeddingError("numpy is required for CSA embedding retrieval") from exc
        if self._cache_valid() and not force:
            self.load()
            return self.stats(cache_hit=True)

        meta_data = json.loads(self.metaop_path.read_text(encoding="utf-8"))
        api_data = json.loads(self.api_path.read_text(encoding="utf-8"))
        meta_records = build_metaop_records(meta_data)
        api_records = build_api_records(api_data)
        encoder = self._encoder_instance()
        meta_embeddings = encoder.encode(
            [record["document"] for record in meta_records],
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        api_embeddings = encoder.encode(
            [record["document"] for record in api_records],
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        np.save(self.cache_dir / "metaop_embeddings.npy", meta_embeddings)
        np.save(self.cache_dir / "api_embeddings.npy", api_embeddings)
        (self.cache_dir / "metaop_records.json").write_text(
            json.dumps(meta_records, ensure_ascii=False), encoding="utf-8")
        (self.cache_dir / "api_records.json").write_text(
            json.dumps(api_records, ensure_ascii=False), encoding="utf-8")
        self.manifest_path.write_text(
            json.dumps(self._fingerprint(), indent=2, ensure_ascii=False), encoding="utf-8")
        self._meta_records, self._api_records = meta_records, api_records
        self._meta_embeddings, self._api_embeddings = meta_embeddings, api_embeddings
        self._last_cache_hit = False
        return self.stats(cache_hit=False)

    def load(self):
        if not self._cache_valid():
            raise CSAEmbeddingError("CSA embedding cache is missing or stale; rebuild it")
        try:
            import numpy as np
        except ImportError as exc:
            raise CSAEmbeddingError("numpy is required for CSA embedding retrieval") from exc
        self._meta_records = json.loads(
            (self.cache_dir / "metaop_records.json").read_text(encoding="utf-8"))
        self._api_records = json.loads(
            (self.cache_dir / "api_records.json").read_text(encoding="utf-8"))
        self._meta_embeddings = np.load(self.cache_dir / "metaop_embeddings.npy")
        self._api_embeddings = np.load(self.cache_dir / "api_embeddings.npy")
        self._last_cache_hit = True
        return self

    @staticmethod
    def _top_k(records, embeddings, query_embedding, count):
        import numpy as np

        if not records or count <= 0:
            return []
        scores = embeddings @ query_embedding
        count = min(int(count), len(records))
        indices = np.argpartition(-scores, count - 1)[:count]
        indices = indices[np.argsort(-scores[indices])]
        results = []
        for index in indices:
            item = dict(records[int(index)]["payload"])
            item["_embedding_id"] = records[int(index)]["id"]
            item["_similarity"] = float(scores[int(index)])
            item["_retrieval"] = "embedding"
            results.append(item)
        return results

    def retrieve(self, query, metaop_top_k=5, api_top_k=8):
        if self._meta_embeddings is None or self._api_embeddings is None:
            if self._cache_valid():
                self.load()
            else:
                self.build()
        encoder = self._encoder_instance()
        query_embedding = encoder.encode(
            [QUERY_PREFIX + str(query)],
            batch_size=1,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        return (
            self._top_k(self._meta_records, self._meta_embeddings, query_embedding, metaop_top_k),
            self._top_k(self._api_records, self._api_embeddings, query_embedding, api_top_k),
        )

    def stats(self, cache_hit=None):
        cache_hit = self._last_cache_hit if cache_hit is None else cache_hit
        return {
            "model": self.model_name_or_path,
            "cache_dir": str(self.cache_dir),
            "metaop_records": len(self._meta_records or []),
            "api_records": len(self._api_records or []),
            "dimensions": int(self._api_embeddings.shape[1]) if self._api_embeddings is not None else 0,
            "cache_hit": cache_hit,
            "fingerprint": self._fingerprint(),
        }
