"""Embedding compression utilities for reducing storage size."""

import numpy as np
from typing import Tuple, Optional, Literal
import struct


class EmbeddingCompressor:
    """
    Compress embeddings using quantization techniques.

    Provides significant storage reduction with minimal quality loss:
    - float32: 384 dims × 4 bytes = 1.5KB per embedding
    - int8: 384 dims × 1 byte = 384 bytes (4x compression, ~98% quality)
    - binary: 384 dims / 8 = 48 bytes (32x compression, ~96% quality)
    """

    @staticmethod
    def quantize_int8(
        embedding: np.ndarray,
        calibration_min: Optional[float] = None,
        calibration_max: Optional[float] = None,
    ) -> Tuple[bytes, float, float]:
        """
        Quantize float32 embedding to int8.

        Args:
            embedding: Float32 numpy array
            calibration_min: Minimum value for scaling (auto-detect if None)
            calibration_max: Maximum value for scaling (auto-detect if None)

        Returns:
            Tuple of (quantized_bytes, min_val, max_val) for dequantization
        """
        if calibration_min is None:
            calibration_min = float(embedding.min())
        if calibration_max is None:
            calibration_max = float(embedding.max())

        # Avoid division by zero
        if calibration_max == calibration_min:
            calibration_max = calibration_min + 1.0

        # Scale to int8 range [-128, 127]
        scale = (calibration_max - calibration_min) / 255.0
        quantized = np.round((embedding - calibration_min) / scale - 128).astype(np.int8)

        return quantized.tobytes(), calibration_min, calibration_max

    @staticmethod
    def dequantize_int8(
        quantized_bytes: bytes, min_val: float, max_val: float, expected_dims: int = 384
    ) -> np.ndarray:
        """
        Dequantize int8 back to float32.

        Args:
            quantized_bytes: Compressed bytes
            min_val: Original minimum value
            max_val: Original maximum value
            expected_dims: Expected embedding dimensions

        Returns:
            Float32 numpy array
        """
        quantized = np.frombuffer(quantized_bytes, dtype=np.int8)
        scale = (max_val - min_val) / 255.0
        return (quantized.astype(np.float32) + 128) * scale + min_val

    @staticmethod
    def quantize_binary(embedding: np.ndarray) -> bytes:
        """
        Binary quantization: threshold at 0.

        Provides 32x compression with ~96% performance retention
        according to HuggingFace research.

        Args:
            embedding: Float32 numpy array

        Returns:
            Packed binary bytes
        """
        # Pack bits into uint8 (8x compression)
        binary = (embedding > 0).astype(np.uint8)
        packed = np.packbits(binary)
        return packed.tobytes()

    @staticmethod
    def dequantize_binary(binary_bytes: bytes, expected_dims: int = 384) -> np.ndarray:
        """
        Dequantize binary back to float32.

        Args:
            binary_bytes: Packed binary bytes
            expected_dims: Expected embedding dimensions

        Returns:
            Float32 numpy array with values -1.0 or 1.0
        """
        packed = np.frombuffer(binary_bytes, dtype=np.uint8)
        binary = np.unpackbits(packed)[:expected_dims]
        # Convert 0/1 to -1.0/1.0
        return binary.astype(np.float32) * 2.0 - 1.0

    @staticmethod
    def compress(
        embedding: np.ndarray, method: Literal["float32", "int8", "binary"] = "int8"
    ) -> Tuple[bytes, dict]:
        """
        Compress embedding using specified method.

        Args:
            embedding: Float32 numpy array
            method: Compression method

        Returns:
            Tuple of (compressed_bytes, metadata_dict)
        """
        if method == "binary":
            compressed = EmbeddingCompressor.quantize_binary(embedding)
            metadata = {"method": "binary", "dims": len(embedding)}
        elif method == "int8":
            compressed, min_val, max_val = EmbeddingCompressor.quantize_int8(embedding)
            metadata = {"method": "int8", "dims": len(embedding), "min": min_val, "max": max_val}
        else:  # float32 - no compression
            compressed = embedding.astype(np.float32).tobytes()
            metadata = {"method": "float32", "dims": len(embedding)}

        return compressed, metadata

    @staticmethod
    def decompress(compressed: bytes, metadata: dict) -> np.ndarray:
        """
        Decompress embedding using stored metadata.

        Args:
            compressed: Compressed bytes
            metadata: Metadata dict from compress()

        Returns:
            Float32 numpy array
        """
        method = metadata.get("method", "float32")
        dims = metadata.get("dims", 384)

        if method == "binary":
            return EmbeddingCompressor.dequantize_binary(compressed, dims)
        elif method == "int8":
            min_val = metadata.get("min", -1.0)
            max_val = metadata.get("max", 1.0)
            return EmbeddingCompressor.dequantize_int8(compressed, min_val, max_val, dims)
        else:  # float32
            return np.frombuffer(compressed, dtype=np.float32)

    @staticmethod
    def estimate_size(
        dims: int = 384, method: Literal["float32", "int8", "binary"] = "int8"
    ) -> int:
        """
        Estimate compressed size in bytes.

        Args:
            dims: Embedding dimensions
            method: Compression method

        Returns:
            Estimated size in bytes
        """
        if method == "binary":
            return (dims + 7) // 8  # Round up to nearest byte
        elif method == "int8":
            return dims + 16  # Include metadata
        else:  # float32
            return dims * 4
