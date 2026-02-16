"""Optimal database configuration settings for Palace Mental."""

# KuzuDB optimal configuration
KUZU_OPTIMAL_CONFIG = {
    # Buffer sizes for large datasets
    'kuzu_node_buffer_size': 1073741824,  # 1GB
    'kuzu_relationship_buffer_size': 536870912,  # 512MB

    # Parallelism settings
    'kuzu_max_num_threads': 8,
    'kuzu_enable_auto_flush': True,

    # Memory management
    'kuzu_buffer_pool_size': 2097152,  # 2MB
    'kuzu_max_db_size': 10737418240,  # 10GB

    # Query optimization
    'kuzu_enable_journaling': True,
    'kuzu_checkpoint_interval': 60000,  # 60 seconds

    # Indexing
    'kuzu_auto_index': True,
    'kuzu_index_memory_limit': 2147483648,  # 2GB
}

# SQLite+vec optimal configuration
SQLITE_OPTIMAL_PRAGMAS = {
    # WAL mode for better concurrency
    'journal_mode': 'WAL',

    # Synchronous mode - balance safety/speed
    'synchronous': 'NORMAL',

    # Aggressive caching
    'cache_size': -1000000,  # 1GB cache (negative value means KB)
    'mmap_size': 1073741824,  # 1GB mmap

    # Temp store in memory
    'temp_store': 'MEMORY',

    # Page size optimal for vectors
    'page_size': 4096,

    # Locking mode
    'locking_mode': 'NORMAL',

    # Optimization settings
    'optimize': '0x10002',  # OPTIMIZE flag
}

# Performance tuning settings
PERFORMANCE_CONFIG = {
    # Batch sizes for bulk operations
    'batch_size_nodes': 100,
    'batch_size_edges': 500,
    'batch_size_embeddings': 1000,

    # Parallelism
    'max_workers_ingestion': None,  # None = cpu_count()
    'max_workers_processing': None,

    # Cache sizes
    'query_cache_size': 1024,
    'edge_weight_cache_size': 2048,
    'artifact_lookup_cache_size': 4096,

    # Thresholds for optimizations
    'vectorization_threshold': 5,  # Use vectorized ops for n >= 5
    'parallel_threshold': 10,  # Use parallel processing for n >= 10
    'large_file_threshold_mb': 50,  # Files larger than this are processed sequentially
}


def get_kuzu_config() -> dict:
    """Get KuzuDB configuration as list of SET statements."""
    return [
        f"SET {key} = {value}"
        for key, value in KUZU_OPTIMAL_CONFIG.items()
    ]


def get_sqlite_pragmas() -> list:
    """Get SQLite pragmas as list of PRAGMA statements."""
    return [
        f"PRAGMA {key} = {value};"
        for key, value in SQLITE_OPTIMAL_PRAGMAS.items()
    ]
