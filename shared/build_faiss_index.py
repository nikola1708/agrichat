#!/usr/bin/env python3
"""
Build FAISS index from a folder of markdown/text documents.
Usage:
  python shared/build_faiss_index.py --src docs --index ./.faiss_index --meta ./.faiss_metadata.json
"""
import argparse
import sys
import logging
from shared import retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Build FAISS index from documents")
    parser.add_argument('--src', required=False, default='docs', help='Source folder with text files')
    parser.add_argument('--index', required=False, default='./.faiss_index', help='Path to save FAISS index')
    parser.add_argument('--meta', required=False, default='./.faiss_metadata.json', help='Path to save metadata JSON')

    args = parser.parse_args()

    try:
        retriever.build_index(args.src, index_path=args.index, metadata_path=args.meta)
        logger.info('Index built and saved to %s and %s', args.index, args.meta)
    except Exception as e:
        logger.exception('Failed to build index: %s', e)
        sys.exit(2)


if __name__ == '__main__':
    main()
