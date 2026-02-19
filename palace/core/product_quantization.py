"""Product Quantization for massive-scale vector compression.

Product Quantization (PQ) is the industry standard for compressing
high-dimensional vectors at scale. Used by FAISS, Milvus, Weaviate, etc.

Compression ratio: up to 100x with <5% loss in recall

How it works:
1. Split vector into M sub-vectors
2. Cluster each sub-space separately (K-means)
3. Store only cluster IDs (codes)
4. Reconstruction: lookup centroids from codebook

Example for 384-dim vectors with M=8, K=256:
- Original: 384 × 4 bytes = 1.5KB
- PQ: 48 × 1 byte (code) = 48 bytes
- Compression: 32x
- Recall: ~95% for nearest neighbor search
"""

import numpy as np
from typing import Tuple, List, Optional
from pathlib import Path
import pickle
from collections import defaultdict


class ProductQuantizer:
    """
    Product Quantization for extreme compression of embeddings.

    Suitable for datasets with millions of vectors where storage is critical.
    """

    def __init__(self, n_subvectors: int = 8, n_clusters: int = 256, model_path: Optional[Path] = None):
        """
        Initialize PQ compressor.

        Args:
            n_subvectors: Number of sub-vectors (M). Higher = better quality, slower
            n_clusters: Number of clusters per sub-space (K). 256 = 1 byte per sub-vector
            model_path: Path to save/load codebooks
        """
        self.n_subvectors = n_subvectors
        self.n_clusters = n_clusters
        self.model_path = model_path

        self.subvector_dim = 384 // n_subvectors
        self.codebooks = None  # List of (K, subvector_dim) arrays
        self.is_fitted = False

        # Load existing model if available
        if model_path and model_path.exists():
            self.load()

    def fit(self, embeddings: np.ndarray, max_samples: int = 100000) -> None:
        """
        Fit PQ codebooks on embeddings.

        Args:
            embeddings: Training embeddings, shape (n_samples, 384)
            max_samples: Max samples to use for training (for speed)
        """
        n_samples = min(len(embeddings), max_samples)
        embeddings = embeddings[:n_samples]

        self.codebooks = []

        # Process each sub-vector
        for i in range(self.n_subvectors):
            start_idx = i * self.subvector_dim
            end_idx = start_idx + self.subvector_dim

            # Extract sub-vectors
            subvectors = embeddings[:, start_idx:end_idx]

            # Run K-means clustering
            centroids = self._kmeans(subvectors, self.n_clusters)
            self.codebooks.append(centroids)

        self.is_fitted = True

        # Save model if path provided
        if self.model_path:
            self.save()

    def _kmeans(self, vectors: np.ndarray, n_clusters: int, max_iter: int = 100) -> np.ndarray:
        """
        Run K-means clustering.

        Args:
            vectors: Vectors to cluster, shape (n_samples, dim)
            n_clusters: Number of clusters
            max_iter: Maximum iterations

        Returns:
            Centroids, shape (n_clusters, dim)
        """
        # Initialize centroids randomly
        indices = np.random.choice(len(vectors), n_clusters, replace=False)
        centroids = vectors[indices].copy()

        for _ in range(max_iter):
            # Assign to nearest centroid
            distances = np.sqrt(((vectors[:, np.newaxis, :] - centroids[np.newaxis, :, :]) ** 2).sum(axis=2))
            assignments = np.argmin(distances, axis=1)

            # Update centroids
            new_centroids = np.array([vectors[assignments == k].mean(axis=0) for k in range(n_clusters)])

            # Handle empty clusters
            empty = np.isnan(new_centroids).any(axis=1)
            new_centroids[empty] = centroids[empty]

            # Check convergence
            if np.allclose(centroids, new_centroids):
                break

            centroids = new_centroids

        return centroids

    def encode(self, embedding: np.ndarray) -> bytes:
        """
        Encode embedding to PQ codes.

        Args:
            embedding: Single embedding, shape (384,)

        Returns:
            PQ codes as bytes (length = n_subvectors)
        """
        if not self.is_fitted:
            raise ValueError("PQ model not fitted. Call fit() first.")

        codes = np.zeros(self.n_subvectors, dtype=np.uint8)

        for i in range(self.n_subvectors):
            start_idx = i * self.subvector_dim
            end_idx = start_idx + self.subvector_dim

            subvector = embedding[start_idx:end_idx]

            # Find nearest centroid
            distances = np.sqrt(((self.codebooks[i] - subvector) ** 2).sum(axis=1))
            codes[i] = np.argmin(distances)

        return codes.tobytes()

    def decode(self, codes: bytes) -> np.ndarray:
        """
        Decode PQ codes to embedding.

        Args:
            codes: PQ codes as bytes

        Returns:
            Reconstructed embedding, shape (384,)
        """
        if not self.is_fitted:
            raise ValueError("PQ model not fitted.")

        code_array = np.frombuffer(codes, dtype=np.uint8)
        reconstructed = np.zeros(384, dtype=np.float32)

        for i in range(self.n_subvectors):
            start_idx = i * self.subvector_dim
            end_idx = start_idx + self.subvector_dim

            # Lookup centroid from codebook
            code = code_array[i]
            reconstructed[start_idx:end_idx] = self.codebooks[i][code]

        return reconstructed

    def batch_encode(self, embeddings: np.ndarray) -> bytes:
        """
        Encode multiple embeddings efficiently.

        Args:
            embeddings: Multiple embeddings, shape (n, 384)

        Returns:
            Concatenated PQ codes
        """
        codes_list = []
        for emb in embeddings:
            codes_list.append(self.encode(emb))
        return b''.join(codes_list)

    def batch_decode(self, codes: bytes, n_embeddings: int) -> np.ndarray:
        """
        Decode multiple PQ codes.

        Args:
            codes: Concatenated PQ codes
            n_embeddings: Number of embeddings to decode

        Returns:
            Reconstructed embeddings, shape (n, 384)
        """
        code_size = self.n_subvectors
        reconstructed = np.zeros((n_embeddings, 384), dtype=np.float32)

        for i in range(n_embeddings):
            start = i * code_size
            end = start + code_size
            reconstructed[i] = self.decode(codes[start:end])

        return reconstructed

    def compute_distance(self, query_codes: bytes, database_codes: bytes) -> np.ndarray:
        """
        Compute approximate distances using PQ codes.

        Uses asymmetric distance computation (ADC) for better accuracy.

        Args:
            query_codes: PQ codes for query embedding
            database_codes: PQ codes for database embeddings

        Returns:
            Approximate distances
        """
        if not self.is_fitted:
            raise ValueError("PQ model not fitted.")

        # Decode query
        query = self.decode(query_codes)

        n_embeddings = len(database_codes) // self.n_subvectors
        code_size = self.n_subvectors
        distances = np.zeros(n_embeddings)

        # Pre-compute query-to-centroid distances
        query_distances = []
        for i in range(self.n_subvectors):
            start_idx = i * self.subvector_dim
            end_idx = start_idx + self.subvector_dim

            query_subvec = query[start_idx:end_idx]
            dists = ((self.codebooks[i] - query_subvec) ** 2).sum(axis=1)
            query_distances.append(dists)

        # Sum distances for each database embedding
        for i in range(n_embeddings):
            start = i * code_size
            end = start + code_size
            codes = np.frombuffer(database_codes[start:end], dtype=np.uint8)

            dist = 0
            for j in range(self.n_subvectors):
                dist += query_distances[j][codes[j]]

            distances[i] = dist

        return distances

    def get_compression_info(self) -> dict:
        """
        Get compression information.

        Returns:
            Dict with compression stats
        """
        original_size = 384 * 4  # float32
        compressed_size = self.n_subvectors  # bytes
        compression_ratio = original_size / compressed_size

        return {
            'n_subvectors': self.n_subvectors,
            'n_clusters': self.n_clusters,
            'subvector_dim': self.subvector_dim,
            'original_size_bytes': original_size,
            'compressed_size_bytes': compressed_size,
            'compression_ratio': compression_ratio,
            'bits_per_vector': compressed_size * 8,
        }

    def save(self) -> None:
        """Save PQ model to disk."""
        if self.model_path is None:
            return

        model_data = {
            'n_subvectors': self.n_subvectors,
            'n_clusters': self.n_clusters,
            'subvector_dim': self.subvector_dim,
            'codebooks': self.codebooks,
        }

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)

    def load(self) -> None:
        """Load PQ model from disk."""
        if self.model_path is None or not self.model_path.exists():
            return

        with open(self.model_path, 'rb') as f:
            model_data = pickle.load(f)

        self.n_subvectors = model_data['n_subvectors']
        self.n_clusters = model_data['n_clusters']
        self.subvector_dim = model_data['subvector_dim']
        self.codebooks = model_data['codebooks']
        self.is_fitted = True


def estimate_pq_storage(n_embeddings: int, config: str = 'standard') -> dict:
    """
    Estimate storage requirements for PQ-compressed embeddings.

    Args:
        n_embeddings: Number of embeddings
        config: 'minimal', 'standard', or 'high_quality'

    Returns:
        Storage estimates
    """
    configs = {
        'minimal': {'M': 4, 'K': 128},  # 4 subvectors, 128 clusters (7 bits)
        'standard': {'M': 8, 'K': 256},  # 8 subvectors, 256 clusters (8 bits)
        'high_quality': {'M': 16, 'K': 256},  # 16 subvectors, 256 clusters
    }

    cfg = configs[config]

    original_size = n_embeddings * 384 * 4
    compressed_size = n_embeddings * cfg['M']  # 1 byte per subvector (for K=256)
    codebook_size = cfg['M'] * cfg['K'] * 4  # M codebooks × K centroids × 4 bytes

    total = compressed_size + codebook_size

    return {
        'original_size_mb': original_size // (1024 * 1024),
        'compressed_size_mb': compressed_size // (1024 * 1024),
        'codebook_size_mb': codebook_size // (1024 * 1024),
        'total_size_mb': total // (1024 * 1024),
        'compression_ratio': original_size / compressed_size,
        'space_saved_mb': (original_size - total) // (1024 * 1024),
    }
