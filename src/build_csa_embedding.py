"""Build the persistent CSA MetaOp/API embedding indexes."""

import argparse
import json
from pathlib import Path

from retriever.csa_embedding import CSAEmbeddingRetriever, DEFAULT_MODEL


REPO_ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metaops", type=Path,
                        default=REPO_ROOT / "csa_official_checker_logic_extract/csa_meat_op.json")
    parser.add_argument("--apis", type=Path,
                        default=REPO_ROOT / "csa_official_api_extract/csa_api.json")
    parser.add_argument("--cache-dir", type=Path,
                        default=REPO_ROOT / "src/embedding_db/csa")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    retriever = CSAEmbeddingRetriever(
        args.metaops, args.apis, args.cache_dir, args.model, batch_size=args.batch_size)
    print(json.dumps(retriever.build(force=args.force), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
