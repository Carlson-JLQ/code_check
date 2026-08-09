import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from retriever.csa_embedding import CSAEmbeddingRetriever


class FakeEncoder:
    def encode(self, texts, **_):
        vectors = []
        for text in texts:
            lowered = text.lower()
            vector = np.array([
                lowered.count("assignment") + lowered.count("condition"),
                lowered.count("malloc") + lowered.count("allocation"),
                lowered.count("stream"),
                0.1,
            ], dtype=np.float32)
            vector /= np.linalg.norm(vector)
            vectors.append(vector)
        return np.stack(vectors)


def metaop_dataset():
    def logic(identifier, text, callback):
        return {
            "id": identifier,
            "applies_to_frontends": ["frontend:test"],
            "callback_context": [callback],
            "kind": "detection",
            "meta_op": text,
            "behavior": {"trigger": [text], "constraints": [], "effects": []},
            "meta_impl": text,
            "source_spans": [],
            "api_refs": [],
            "depends_on": [],
        }

    return {"checkers": [{
        "id": "checker:test",
        "implementation_class": "TestChecker",
        "summary": "test checker",
        "analysis_mode": "path_sensitive",
        "frontends": [{"id": "frontend:test", "name": "test.Checker"}],
        "logic_units": [
            logic("logic:assignment", "detect assignment in branch condition", "ASTCodeBody"),
            logic("logic:malloc", "track malloc allocation state", "PostCall"),
        ],
    }]}


class CSAEmbeddingTest(unittest.TestCase):
    def test_build_retrieve_and_cache_fingerprint(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            meta_path, api_path = root / "meta.json", root / "api.json"
            meta_path.write_text(json.dumps(metaop_dataset()), encoding="utf-8")
            api_path.write_text(json.dumps({
                "apis": [
                    {"id": "api:assign", "kind": "method", "name": "isAssignmentOp",
                     "qualified_name": "clang::BinaryOperator::isAssignmentOp",
                     "comment": "test whether an operator is an assignment"},
                    {"id": "api:malloc", "kind": "function", "name": "malloc",
                     "qualified_name": "malloc", "comment": "allocate memory"},
                ],
                "types": [],
            }), encoding="utf-8")
            retriever = CSAEmbeddingRetriever(
                meta_path, api_path, root / "cache", "fake-model",
                encoder_factory=lambda _: FakeEncoder())
            stats = retriever.build()
            metaops, apis = retriever.retrieve("assignment inside an if condition", 1, 1)
            self.assertFalse(stats["cache_hit"])
            self.assertEqual(stats["dimensions"], 4)
            self.assertEqual(metaops[0]["_embedding_id"], "logic:assignment")
            self.assertEqual(apis[0]["qualified_name"], "clang::BinaryOperator::isAssignmentOp")
            self.assertEqual(metaops[0]["_retrieval"], "embedding")

            cached = CSAEmbeddingRetriever(
                meta_path, api_path, root / "cache", "fake-model",
                encoder_factory=lambda _: (_ for _ in ()).throw(AssertionError("model loaded")))
            self.assertTrue(cached.build()["cache_hit"])

            api_path.write_text(json.dumps({"apis": [], "types": []}), encoding="utf-8")
            self.assertFalse(cached._cache_valid())


if __name__ == "__main__":
    unittest.main()
