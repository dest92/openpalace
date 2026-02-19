"""PCA-based dimensionality reduction for massive-scale embedding storage.

For projects with millions of artifacts, storing 384-dimensional embeddings
is prohibitive. PCA reduces dimensions while preserving ~95% variance.

Original: 384 dims × 4 bytes = 1.5KB per embedding
PCA-128:  128 dims × 4 bytes = 512 bytes per embedding (3x compression)
PCA-64:   64 dims × 4 bytes = 256 bytes per embedding (6x compression)
"""

import numpy as np
from typing import Tuple, Optional
from pathlib import Path
import pickle


class PCACompressor:
    """
    Dimensionality reduction using Principal Component Analysis.

    Maintains a fitted PCA model that can be applied to new embeddings.
    Model is persisted to disk for reuse across sessions.
    """

    def __init__(self, n_components: int = 128, model_path: Optional[Path] = None):
        """
        Initialize PCA compressor.

        Args:
            n_components: Target dimensions (64, 128, or 256)
            model_path: Path to save/load PCA model
        """
        self.n_components = n_components
        self.model_path = model_path
        self.components = None
        self.mean = None
        self.explained_variance = None

        # Load existing model if available
        if model_path and model_path.exists():
            self.load()

    def fit(self, embeddings: np.ndarray) -> None:
        """
        Fit PCA model on sample embeddings.

        Should be called with a representative sample (1000-10000 embeddings)
        from the codebase before using transform.

        Args:
            embeddings: Array of shape (n_samples, 384)
        """
        # Center the data
        self.mean = np.mean(embeddings, axis=0)
        centered = embeddings - self.mean

        # Compute covariance matrix
        cov = np.cov(centered.T)

        # Eigen decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(cov)

        # Sort by eigenvalue (descending)
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Store top components
        self.components = eigenvectors[:, :self.n_components]
        self.explained_variance = eigenvalues[:self.n_components]

        # Save model if path provided
        if self.model_path:
            self.save()

    def transform(self, embedding: np.ndarray) -> np.ndarray:
        """
        Transform embedding to reduced dimensions.

        Args:
            embedding: Original 384-dim embedding

        Returns:
            Reduced dimension embedding
        """
        if self.components is None:
            raise ValueError("PCA model not fitted. Call fit() first.")

        centered = embedding - self.mean
        return np.dot(centered, self.components)

    def fit_transform(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Fit model and transform embeddings.

        Args:
            embeddings: Array of shape (n_samples, 384)

        Returns:
            Transformed embeddings of shape (n_samples, n_components)
        """
        self.fit(embeddings)
        return self.transform(embeddings)

    def inverse_transform(self, reduced: np.ndarray) -> np.ndarray:
        """
        Reconstruct embedding from reduced dimensions.

        Note: Reconstruction is lossy.

        Args:
            reduced: Reduced dimension embedding

        Returns:
            Reconstructed 384-dim embedding
        """
        if self.components is None:
            raise ValueError("PCA model not fitted.")

        return np.dot(reduced, self.components.T) + self.mean

    def save(self) -> None:
        """Save PCA model to disk."""
        if self.model_path is None:
            return

        model_data = {
            'components': self.components,
            'mean': self.mean,
            'explained_variance': self.explained_variance,
            'n_components': self.n_components,
        }

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)

    def load(self) -> None:
        """Load PCA model from disk."""
        if self.model_path is None or not self.model_path.exists():
            return

        with open(self.model_path, 'rb') as f:
            model_data = pickle.load(f)

        self.components = model_data['components']
        self.mean = model_data['mean']
        self.explained_variance = model_data.get('explained_variance')
        self.n_components = model_data['n_components']

    def get_compression_ratio(self) -> float:
        """Calculate compression ratio."""
        return 384 / self.n_components

    def estimate_storage_saved(self, n_embeddings: int) -> Tuple[int, int]:
        """
        Estimate storage savings for n embeddings.

        Returns:
            (original_size_bytes, compressed_size_bytes)
        """
        original = n_embeddings * 384 * 4  # float32
        compressed = n_embeddings * self.n_components * 4
        return original, compressed


def recommended_components(dataset_size: int) -> int:
    """
    Recommend number of PCA components based on dataset size.

    For massive datasets, use more aggressive reduction.

    Args:
        dataset_size: Number of embeddings in the dataset

    Returns:
        Recommended n_components
    """
    if dataset_size < 1000:
        return 256  # Small: preserve more info
    elif dataset_size < 10000:
        return 128  # Medium: balance
    elif dataset_size < 100000:
        return 96   # Large: aggressive
    else:
        return 64   # Massive: very aggressive
