"""Benchmark script to measure optimization improvements."""

import time
import tempfile
import numpy as np
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.ingest.pipeline import BigBangPipeline


def benchmark_batch_operations():
    """Benchmark batch vs individual operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        palace_dir = Path(tmpdir) / ".palace"

        with Hippocampus(palace_dir) as hippo:
            hippo.initialize_schema()

            # Generate test data
            nodes = [{"id": f"node_{i}", "name": f"Node {i}"} for i in range(100)]

            # Benchmark individual operations
            start = time.time()
            for node in nodes:
                try:
                    hippo.create_node(
                        "Concept",
                        {
                            **node,
                            "embedding_id": f"emb_{node['id']}",
                            "layer": "test",
                            "stability": 0.5,
                        },
                    )
                except Exception:
                    pass
            individual_time = time.time() - start

            print(f"Individual operations (100 nodes): {individual_time:.3f}s")

        # Fresh database for batch test
        with Hippocampus(palace_dir) as hippo:
            hippo.initialize_schema()

            # Prepare batch data
            batch_nodes = [
                {
                    "id": f"batch_node_{i}",
                    "name": f"Batch Node {i}",
                    "embedding_id": f"emb_{i}",
                    "layer": "test",
                    "stability": 0.5,
                }
                for i in range(100)
            ]

            # Benchmark batch operations
            start = time.time()
            hippo.create_nodes_batch("Concept", batch_nodes)
            batch_time = time.time() - start

            print(f"Batch operations (100 nodes): {batch_time:.3f}s")
            print(f"Speedup: {individual_time / batch_time:.1f}x")


def benchmark_similarity_search():
    """Benchmark similarity search performance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        palace_dir = Path(tmpdir) / ".palace"

        with Hippocampus(palace_dir) as hippo:
            hippo.initialize_schema()

            # Insert test embeddings
            print("Inserting 100 test embeddings...")
            for i in range(100):
                embedding = np.random.randn(384).astype(np.float32)
                hippo.store_embedding(f"emb_{i}", embedding)

            # Benchmark similarity search
            query = np.random.randn(384).astype(np.float32)

            start = time.time()
            results = hippo.similarity_search(query, top_k=10)
            search_time = time.time() - start

            print(f"Similarity search (100 embeddings): {search_time * 1000:.2f}ms")
            print(f"Found {len(results)} results")


def benchmark_compression():
    """Benchmark embedding compression."""
    from palace.core.compression import EmbeddingCompressor

    # Generate test embedding
    embedding = np.random.randn(384).astype(np.float32)

    print("\nCompression benchmarks:")
    print(f"Original size: {embedding.nbytes} bytes ({embedding.nbytes / 1024:.2f}KB)")

    # Test int8 compression
    compressed, metadata = EmbeddingCompressor.compress(embedding, "int8")
    print(
        f"int8 compressed: {len(compressed)} bytes ({len(compressed) / embedding.nbytes * 100:.1f}% of original)"
    )

    # Test binary compression
    compressed, metadata = EmbeddingCompressor.compress(embedding, "binary")
    print(
        f"Binary compressed: {len(compressed)} bytes ({len(compressed) / embedding.nbytes * 100:.1f}% of original)"
    )

    # Verify decompression quality
    compressed, metadata = EmbeddingCompressor.compress(embedding, "int8")
    decompressed = EmbeddingCompressor.decompress(compressed, metadata)

    # Calculate cosine similarity
    similarity = np.dot(embedding, decompressed) / (
        np.linalg.norm(embedding) * np.linalg.norm(decompressed)
    )
    print(f"Decompression quality (cosine similarity): {similarity:.4f}")


if __name__ == "__main__":
    print("=" * 60)
    print("OpenPalace Optimization Benchmark")
    print("=" * 60)

    print("\n1. Batch Operations Benchmark:")
    benchmark_batch_operations()

    print("\n2. Similarity Search Benchmark:")
    benchmark_similarity_search()

    print("\n3. Compression Benchmark:")
    benchmark_compression()

    print("\n" + "=" * 60)
    print("Benchmark complete!")
    print("=" * 60)
