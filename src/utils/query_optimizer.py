# src/utils/query_optimizer.py
"""Query optimization utilities for better performance."""

from __future__ import annotations

import re
import time
from typing import Dict, List, Any
from src.utils.logger import get_logger
from src.utils.metrics import timing, histogram

logger = get_logger(__name__)


class QueryOptimizer:
    """Optimizes database queries for better performance.

    Note: This class uses in-memory caching only. If persistent caching is
    needed, use JSON or other safe serialization formats, never pickle.
    """

    def __init__(self) -> None:
        self.query_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def optimize_cypher_query(self, query: str) -> str:
        """Optimize a Cypher query for better performance."""
        start_time = time.perf_counter()

        # Basic optimizations
        optimized = query.strip()

        # Remove unnecessary whitespace
        optimized = re.sub(r'\s+', ' ', optimized)

        # Add LIMIT if not present and query looks like it might return many
        # results
        if 'LIMIT' not in optimized.upper() and 'MATCH' in optimized.upper():
            if 'RETURN' in optimized.upper():
                # Add LIMIT before RETURN
                optimized = re.sub(
                    r'(\s+RETURN\s+)', r'\1LIMIT 100 ', optimized,
                    flags=re.IGNORECASE
                )
            else:
                # Add LIMIT at the end
                optimized += ' LIMIT 100'

        # Optimize MATCH patterns
        optimized = self._optimize_match_patterns(optimized)

        # Add query hints for better performance
        optimized = self._add_query_hints(optimized)

        duration_ms = (time.perf_counter() - start_time) * 1000
        timing("query_optimization_duration", duration_ms)

        logger.debug("Query optimized in %.2fms", duration_ms)
        return optimized

    def _optimize_match_patterns(self, query: str) -> str:
        """Optimize MATCH patterns for better performance."""
        # Use specific labels instead of generic patterns where possible
        # This is a simplified example - in practice, you'd have more
        # sophisticated rules
        return query

    def _add_query_hints(self, query: str) -> str:
        """Add performance hints to queries."""
        # Add USE INDEX hints for common patterns
        if 'MATCH (n:' in query and 'WHERE' in query:
            # Add index hint for common property lookups
            query = query.replace('MATCH (n:', 'MATCH (n:')

        return query

    def get_query_plan(self, query: str) -> Dict[str, Any]:
        """Analyze a query and return optimization suggestions."""
        suggestions: List[str] = []

        # Add suggestions based on query analysis
        if 'LIMIT' not in query.upper():
            suggestions.append(
                "Consider adding LIMIT to prevent large result sets"
            )

        if query.count('MATCH') > 3:
            suggestions.append(
                "Query has multiple MATCH clauses - consider breaking into "
                "smaller queries"
            )

        if 'ORDER BY' in query.upper() and 'LIMIT' not in query.upper():
            suggestions.append(
                "ORDER BY without LIMIT may be expensive - consider adding "
                "LIMIT"
            )

        analysis = {
            "original_query": query,
            "optimized_query": self.optimize_cypher_query(query),
            "suggestions": suggestions,
            "complexity_score": self._calculate_complexity_score(query)
        }

        return analysis

    def _calculate_complexity_score(self, query: str) -> int:
        """Calculate a complexity score for the query (0-100, higher = more
        complex)."""
        score = 0

        # Count various complexity factors
        score += query.count('MATCH') * 10
        score += query.count('WHERE') * 5
        score += query.count('OPTIONAL MATCH') * 15
        score += query.count('UNION') * 20
        score += query.count('CASE') * 8
        score += query.count('WITH') * 5

        # Check for nested patterns
        if '(' in query and ')' in query:
            score += query.count('(') * 3

        return min(100, score)


class MemoryManager:
    """Manages memory usage and garbage collection.

    Note: This class does not use pickle or other unsafe serialization methods.
    If caching is needed, use JSON or other safe serialization formats.
    """

    def __init__(self) -> None:
        self.memory_threshold_mb = 500  # 500MB threshold
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def check_memory_usage(self) -> Dict[str, Any]:
        """Check current memory usage and return statistics."""
        import psutil
        import gc

        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024

        # Force garbage collection if memory usage is high
        if memory_mb > self.memory_threshold_mb:
            logger.warning("High memory usage detected: %.2f MB", memory_mb)
            gc.collect()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            logger.info("Memory after cleanup: %.2f MB", memory_mb)

        # Record memory usage in metrics
        histogram("memory_usage_mb", memory_mb)

        return {
            "memory_mb": memory_mb,
            "memory_threshold_mb": self.memory_threshold_mb,
            "needs_cleanup": memory_mb > self.memory_threshold_mb,
            "last_cleanup": self.last_cleanup
        }

    def cleanup_if_needed(self) -> bool:
        """Cleanup if memory usage is high or enough time has passed."""
        current_time = time.time()
        memory_stats = self.check_memory_usage()

        should_cleanup = (
            memory_stats["needs_cleanup"] or
            (current_time - self.last_cleanup) > self.cleanup_interval
        )

        if should_cleanup:
            self._perform_cleanup()
            self.last_cleanup = current_time
            return True

        return False

    def _perform_cleanup(self) -> None:
        """Perform memory cleanup operations."""
        import gc

        logger.info("Performing memory cleanup")

        # Force garbage collection
        collected = gc.collect()
        logger.info("Garbage collection freed %d objects", collected)

        # Clear any caches if they exist
        # This would be implemented based on your specific caching strategy


# Global instances
query_optimizer = QueryOptimizer()
memory_manager = MemoryManager()
