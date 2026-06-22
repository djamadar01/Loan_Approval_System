"""
Database optimization module for application history database.

Provides comprehensive optimization features including:
1. Index definitions and query optimization
2. Execution plan analysis
3. Connection pooling configuration
4. Lazy loading for large datasets
5. Pagination helpers with efficiency metrics
"""

import sqlite3
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Generator, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class IndexType(Enum):
    """Index type classifications."""
    SINGLE_COLUMN = "single_column"
    COMPOSITE = "composite"
    COVERING = "covering"
    FULL_TEXT = "full_text"


@dataclass
class IndexDefinition:
    """Index definition with metadata and usage information."""
    name: str
    columns: List[str]
    table: str
    index_type: IndexType
    sql: str
    description: str
    query_patterns: List[str] = field(default_factory=list)
    estimated_size_kb: Optional[float] = None
    usage_count: int = 0

    def create_sql(self) -> str:
        """Return SQL statement to create this index."""
        return self.sql

    def get_info(self) -> Dict[str, Any]:
        """Get index information as dictionary."""
        return {
            "name": self.name,
            "table": self.table,
            "columns": self.columns,
            "type": self.index_type.value,
            "description": self.description,
            "query_patterns": self.query_patterns
        }


class QueryOptimizationProfile:
    """
    Execution plan analysis and optimization recommendations.

    Analyzes SQLite query execution plans and provides performance metrics.
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize query optimizer.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn
        self.execution_plans: Dict[str, Any] = {}

    def analyze_query(self, query: str, params: List[Any] = None) -> Dict[str, Any]:
        """
        Analyze query execution plan and performance.

        Args:
            query: SQL query to analyze
            params: Query parameters

        Returns:
            Dictionary with execution plan details and recommendations
        """
        if params is None:
            params = []

        plan_info = {
            "query": query,
            "params": params,
            "plan": [],
            "recommendations": [],
            "estimated_rows": 0,
            "index_usage": []
        }

        try:
            # Get EXPLAIN QUERY PLAN
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            cursor = self.conn.execute(explain_query, params)
            plan_rows = cursor.fetchall()

            plan_info["plan"] = [dict(row) for row in plan_rows] if plan_rows else []

            # Analyze plan for recommendations
            plan_text = str(plan_rows)

            if "FULL SCAN" in plan_text:
                plan_info["recommendations"].append(
                    "⚠️ FULL TABLE SCAN detected. Consider adding an index on filter columns."
                )

            if "SEARCH" in plan_text:
                plan_info["recommendations"].append(
                    "✓ Index being used for search operation."
                )

            # Get statistical information
            stats = self._get_query_stats(query, params)
            plan_info.update(stats)

        except Exception as e:
            plan_info["error"] = str(e)
            logger.error(f"Error analyzing query: {e}")

        self.execution_plans[query] = plan_info
        return plan_info

    def _get_query_stats(self, query: str, params: List[Any]) -> Dict[str, Any]:
        """Get query statistics."""
        stats = {
            "estimated_rows": 0,
            "index_usage": []
        }

        try:
            # Simple execution to get actual row count
            cursor = self.conn.execute(query, params)
            rows = cursor.fetchall()
            stats["estimated_rows"] = len(rows)
        except Exception as e:
            logger.debug(f"Could not get query stats: {e}")

        return stats

    def get_index_coverage(self) -> Dict[str, Any]:
        """
        Analyze which indexes exist and their coverage.

        Returns:
            Dictionary with index coverage information
        """
        cursor = self.conn.execute("""
            SELECT name, tbl_name, sql
            FROM sqlite_master
            WHERE type='index' AND tbl_name IS NOT NULL
        """)

        indexes = cursor.fetchall()
        coverage = {
            "total_indexes": len(indexes),
            "by_table": {},
            "indexes": []
        }

        for index in indexes:
            idx_info = {
                "name": index[0],
                "table": index[1],
                "sql": index[2]
            }
            coverage["indexes"].append(idx_info)

            if index[1] not in coverage["by_table"]:
                coverage["by_table"][index[1]] = []
            coverage["by_table"][index[1]].append(index[0])

        return coverage

    def suggest_indexes(self) -> List[Dict[str, Any]]:
        """
        Suggest missing indexes based on common query patterns.

        Returns:
            List of suggested index definitions
        """
        suggestions = []

        # Analyze common WHERE clause columns that might benefit from indexes
        tables_info = self._get_table_info()

        for table_name, columns in tables_info.items():
            if table_name.startswith("_"):
                continue

            # Suggest indexes for text fields used in filtering
            for col in columns:
                if col["type"] in ("TEXT", "VARCHAR"):
                    suggestions.append({
                        "table": table_name,
                        "column": col["name"],
                        "reason": "Text column commonly used in WHERE clauses",
                        "priority": "medium"
                    })

        return suggestions

    def _get_table_info(self) -> Dict[str, List[Dict[str, str]]]:
        """Get information about all tables and their columns."""
        tables = {}
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'"
        )

        for (table_name,) in cursor.fetchall():
            cursor = self.conn.execute(f"PRAGMA table_info({table_name})")
            tables[table_name] = [
                {"name": row[1], "type": row[2]}
                for row in cursor.fetchall()
            ]

        return tables

    def get_recommendations(self) -> List[str]:
        """
        Get overall database optimization recommendations.

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check for missing indexes
        coverage = self.get_index_coverage()
        if coverage["total_indexes"] < 5:
            recommendations.append(
                f"Current database has {coverage['total_indexes']} indexes. "
                "Consider adding more indexes for frequently queried columns."
            )

        # Check database size
        cursor = self.conn.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0]
        if db_size > 100 * 1024 * 1024:  # >100MB
            recommendations.append(
                "Large database detected. Consider archiving old records or implementing partitioning."
            )

        # Check for unused tables
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        if len(tables) > 5:
            recommendations.append(
                f"Database has {len(tables)} tables. Review if all are actively used."
            )

        return recommendations


class ConnectionPoolConfig:
    """Configuration and monitoring for connection pooling."""

    @dataclass
    class PoolSettings:
        """Connection pool configuration settings."""
        pool_size: int = 5
        timeout: float = 30.0
        check_same_thread: bool = False
        isolation_level: Optional[str] = None
        journal_mode: str = "WAL"
        synchronous: str = "NORMAL"
        cache_size: int = 2000
        temp_store: str = "MEMORY"
        mmap_size: int = 30000000  # 30MB memory mapping
        query_timeout: int = 5000  # milliseconds

    def __init__(self):
        """Initialize pool configuration."""
        self.settings = self.PoolSettings()
        self.connection_stats = {
            "total_acquired": 0,
            "total_released": 0,
            "active_connections": 0,
            "peak_connections": 0,
            "total_queries": 0,
            "slow_queries": 0
        }

    def get_optimized_pragmas(self) -> List[Tuple[str, Any]]:
        """
        Get recommended PRAGMA statements for optimization.

        Returns:
            List of (pragma_name, value) tuples
        """
        return [
            ("PRAGMA journal_mode", self.settings.journal_mode),
            ("PRAGMA synchronous", self.settings.synchronous),
            ("PRAGMA cache_size", f"-{self.settings.cache_size}"),
            ("PRAGMA temp_store", self.settings.temp_store),
            ("PRAGMA foreign_keys", "ON"),
            ("PRAGMA query_only", "OFF"),
            ("PRAGMA mmap_size", self.settings.mmap_size),
            ("PRAGMA busy_timeout", self.settings.query_timeout),
            ("PRAGMA auto_vacuum", "INCREMENTAL"),
            ("PRAGMA incremental_vacuum", "1000"),
        ]

    def apply_pragmas(self, conn: sqlite3.Connection) -> None:
        """
        Apply optimization pragmas to connection.

        Args:
            conn: SQLite connection
        """
        for pragma, value in self.get_optimized_pragmas():
            try:
                conn.execute(f"{pragma}={value}")
                logger.debug(f"Applied {pragma}={value}")
            except Exception as e:
                logger.warning(f"Could not apply {pragma}: {e}")

    def record_acquisition(self) -> None:
        """Record connection acquisition."""
        self.connection_stats["total_acquired"] += 1
        self.connection_stats["active_connections"] += 1
        peak = self.connection_stats["peak_connections"]
        active = self.connection_stats["active_connections"]
        if active > peak:
            self.connection_stats["peak_connections"] = active

    def record_release(self) -> None:
        """Record connection release."""
        self.connection_stats["total_released"] += 1
        self.connection_stats["active_connections"] = max(
            0, self.connection_stats["active_connections"] - 1
        )

    def record_query(self, duration_ms: float) -> None:
        """
        Record query execution.

        Args:
            duration_ms: Query duration in milliseconds
        """
        self.connection_stats["total_queries"] += 1
        if duration_ms > 100:  # Slow query threshold
            self.connection_stats["slow_queries"] += 1
            logger.warning(f"Slow query detected: {duration_ms}ms")

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            **self.connection_stats,
            "settings": {
                "pool_size": self.settings.pool_size,
                "timeout": self.settings.timeout,
                "journal_mode": self.settings.journal_mode,
                "synchronous": self.settings.synchronous,
                "cache_size": self.settings.cache_size
            }
        }


class LazyLoader:
    """
    Lazy loading mechanism for large datasets.

    Implements lazy evaluation and streaming for memory-efficient data retrieval.
    """

    def __init__(self, conn: sqlite3.Connection, batch_size: int = 1000):
        """
        Initialize lazy loader.

        Args:
            conn: SQLite database connection
            batch_size: Number of rows to fetch per batch
        """
        self.conn = conn
        self.batch_size = batch_size

    @contextmanager
    def lazy_query(
        self,
        query: str,
        params: List[Any] = None
    ) -> Generator[List[sqlite3.Row], None, None]:
        """
        Execute query with lazy loading.

        Yields batches of rows instead of loading entire result set.

        Args:
            query: SQL query
            params: Query parameters

        Yields:
            Batches of sqlite3.Row objects
        """
        if params is None:
            params = []

        try:
            cursor = self.conn.execute(query, params)
            while True:
                rows = cursor.fetchmany(self.batch_size)
                if not rows:
                    break
                yield rows
        except Exception as e:
            logger.error(f"Error in lazy query: {e}")
            raise

    def lazy_iterator(
        self,
        query: str,
        params: List[Any] = None
    ) -> Generator[sqlite3.Row, None, None]:
        """
        Get iterator over query results one row at a time.

        Args:
            query: SQL query
            params: Query parameters

        Yields:
            Individual sqlite3.Row objects
        """
        if params is None:
            params = []

        cursor = self.conn.execute(query, params)
        for row in cursor:
            yield row

    def stream_to_file(
        self,
        query: str,
        filepath: str,
        params: List[Any] = None,
        format_func=None
    ) -> int:
        """
        Stream query results directly to file.

        Args:
            query: SQL query
            filepath: Output file path
            params: Query parameters
            format_func: Optional function to format each row

        Returns:
            Number of rows written
        """
        if params is None:
            params = []

        row_count = 0
        try:
            with open(filepath, 'w') as f:
                for row in self.lazy_iterator(query, params):
                    if format_func:
                        line = format_func(row)
                    else:
                        line = str(dict(row))
                    f.write(line + '\n')
                    row_count += 1
        except Exception as e:
            logger.error(f"Error streaming to file: {e}")
            raise

        return row_count


class PaginationHelper:
    """
    Pagination helper with efficiency metrics and optimization.

    Implements efficient pagination with cursor-based and offset-based options.
    """

    @dataclass
    class PageResult:
        """Result of pagination query."""
        items: List[Any]
        total_count: int
        page_number: int
        page_size: int
        total_pages: int
        has_next: bool
        has_previous: bool
        elapsed_ms: float = 0.0

        def get_info(self) -> Dict[str, Any]:
            """Get pagination info as dictionary."""
            return {
                "page": self.page_number,
                "page_size": self.page_size,
                "total_items": self.total_count,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_previous": self.has_previous,
                "items_in_page": len(self.items),
                "query_time_ms": self.elapsed_ms
            }

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize pagination helper.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    def paginate(
        self,
        query: str,
        count_query: str,
        params: List[Any],
        page: int = 1,
        page_size: int = 20,
        order_by: str = "id ASC"
    ) -> PageResult:
        """
        Get paginated results with optimized count query.

        Args:
            query: Base SELECT query (without LIMIT/OFFSET)
            count_query: Optimized count query for total
            params: Query parameters
            page: Page number (1-indexed)
            page_size: Items per page
            order_by: ORDER BY clause

        Returns:
            PageResult with items and pagination metadata
        """
        import time
        start_time = time.time()

        # Get total count
        try:
            cursor = self.conn.execute(count_query, params)
            total_count = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting count: {e}")
            total_count = 0

        # Calculate offset
        offset = (page - 1) * page_size
        total_pages = (total_count + page_size - 1) // page_size

        # Get page data
        paginated_query = f"{query} ORDER BY {order_by} LIMIT ? OFFSET ?"
        paginated_params = params + [page_size, offset]

        try:
            cursor = self.conn.execute(paginated_query, paginated_params)
            items = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting page data: {e}")
            items = []

        elapsed_ms = (time.time() - start_time) * 1000

        return self.PageResult(
            items=items,
            total_count=total_count,
            page_number=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
            elapsed_ms=elapsed_ms
        )

    def cursor_paginate(
        self,
        query: str,
        params: List[Any],
        cursor_column: str = "id",
        page_size: int = 20,
        after_cursor: Optional[str] = None
    ) -> PageResult:
        """
        Cursor-based pagination (more efficient for large datasets).

        Args:
            query: Base SELECT query
            params: Query parameters
            cursor_column: Column to use for cursor
            page_size: Items per page
            after_cursor: Cursor value to start after

        Returns:
            PageResult with items and cursor for next page
        """
        import time
        start_time = time.time()

        # Add cursor condition if provided
        cursor_query = query
        cursor_params = params.copy()

        if after_cursor is not None:
            cursor_query += f" AND {cursor_column} > ?"
            cursor_params.append(after_cursor)

        # Get page + 1 to determine if there's a next page
        fetch_size = page_size + 1
        paginated_query = f"{cursor_query} ORDER BY {cursor_column} ASC LIMIT ?"
        paginated_params = cursor_params + [fetch_size]

        cursor = self.conn.execute(paginated_query, paginated_params)
        rows = cursor.fetchall()

        has_next = len(rows) > page_size
        items = rows[:page_size]

        next_cursor = None
        if has_next and items:
            next_cursor = str(dict(items[-1])[cursor_column])

        elapsed_ms = (time.time() - start_time) * 1000

        result = self.PageResult(
            items=items,
            total_count=len(items),
            page_number=1,
            page_size=page_size,
            total_pages=1 if not has_next else 2,
            has_next=has_next,
            has_previous=after_cursor is not None,
            elapsed_ms=elapsed_ms
        )

        # Add cursor info
        result.next_cursor = next_cursor if has_next else None

        return result


class IndexOptimizationRegistry:
    """
    Registry of pre-defined index definitions for common queries.

    Maintains optimal index configuration for the applications table.
    """

    def __init__(self):
        """Initialize index registry with application-specific indexes."""
        self.indexes: Dict[str, IndexDefinition] = {}
        self._register_default_indexes()

    def _register_default_indexes(self) -> None:
        """Register pre-optimized indexes for common queries."""

        # Status filtering index
        self.indexes["idx_status"] = IndexDefinition(
            name="idx_applications_status",
            columns=["status"],
            table="applications",
            index_type=IndexType.SINGLE_COLUMN,
            sql="CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)",
            description="For filtering applications by status (applied, interview, rejected, offer)",
            query_patterns=["WHERE status = ?", "WHERE status IN (...)"],
        )

        # Company filtering index
        self.indexes["idx_company"] = IndexDefinition(
            name="idx_applications_company",
            columns=["company_name"],
            table="applications",
            index_type=IndexType.SINGLE_COLUMN,
            sql="CREATE INDEX IF NOT EXISTS idx_applications_company ON applications(company_name)",
            description="For filtering by company name",
            query_patterns=["WHERE company_name = ?", "WHERE company_name LIKE ?"],
        )

        # Date filtering index
        self.indexes["idx_created_at"] = IndexDefinition(
            name="idx_applications_created_at",
            columns=["created_at"],
            table="applications",
            index_type=IndexType.SINGLE_COLUMN,
            sql="CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications(created_at DESC)",
            description="For ordering by creation date and date range filtering",
            query_patterns=["ORDER BY created_at DESC", "WHERE created_at BETWEEN ? AND ?"],
        )

        # Composite index for status + created_at (common combined filter)
        self.indexes["idx_status_created"] = IndexDefinition(
            name="idx_applications_status_created",
            columns=["status", "created_at"],
            table="applications",
            index_type=IndexType.COMPOSITE,
            sql="CREATE INDEX IF NOT EXISTS idx_applications_status_created ON applications(status, created_at DESC)",
            description="Composite index for queries filtering by status and sorted by date",
            query_patterns=["WHERE status = ? ORDER BY created_at DESC"],
        )

        # Match score index for ranking queries
        self.indexes["idx_match_score"] = IndexDefinition(
            name="idx_applications_match_score",
            columns=["match_score"],
            table="applications",
            index_type=IndexType.SINGLE_COLUMN,
            sql="CREATE INDEX IF NOT EXISTS idx_applications_match_score ON applications(match_score DESC)",
            description="For sorting/filtering by match score",
            query_patterns=["ORDER BY match_score DESC", "WHERE match_score > ?"],
        )

        # Job title index for search
        self.indexes["idx_job_title"] = IndexDefinition(
            name="idx_applications_job_title",
            columns=["job_title"],
            table="applications",
            index_type=IndexType.SINGLE_COLUMN,
            sql="CREATE INDEX IF NOT EXISTS idx_applications_job_title ON applications(job_title)",
            description="For job title filtering and search",
            query_patterns=["WHERE job_title LIKE ?", "WHERE job_title = ?"],
        )

        # Location index
        self.indexes["idx_location"] = IndexDefinition(
            name="idx_applications_location",
            columns=["location"],
            table="applications",
            index_type=IndexType.SINGLE_COLUMN,
            sql="CREATE INDEX IF NOT EXISTS idx_applications_location ON applications(location)",
            description="For filtering by job location",
            query_patterns=["WHERE location = ?", "WHERE location LIKE ?"],
        )

    def get_all_indexes(self) -> List[IndexDefinition]:
        """Get all registered indexes."""
        return list(self.indexes.values())

    def get_index(self, name: str) -> Optional[IndexDefinition]:
        """Get index by name."""
        return self.indexes.get(name)

    def get_indexes_for_table(self, table: str) -> List[IndexDefinition]:
        """Get all indexes for a specific table."""
        return [idx for idx in self.indexes.values() if idx.table == table]

    def create_all_indexes(self, conn: sqlite3.Connection) -> Dict[str, bool]:
        """
        Create all indexes in the registry.

        Args:
            conn: SQLite connection

        Returns:
            Dictionary mapping index names to creation success status
        """
        results = {}
        for index_def in self.indexes.values():
            try:
                conn.execute(index_def.sql)
                conn.commit()
                results[index_def.name] = True
                logger.info(f"Created index: {index_def.name}")
            except Exception as e:
                results[index_def.name] = False
                logger.error(f"Failed to create index {index_def.name}: {e}")

        return results

    def get_index_recommendations(self) -> Dict[str, Any]:
        """Get index recommendations with descriptions."""
        return {
            "total_indexes": len(self.indexes),
            "indexes": [idx.get_info() for idx in self.indexes.values()]
        }


class DatabaseOptimizer:
    """
    High-level database optimizer combining all optimization features.

    Orchestrates optimization tasks including indexing, query analysis,
    connection pooling, lazy loading, and pagination.
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize database optimizer.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn
        self.index_registry = IndexOptimizationRegistry()
        self.query_profile = QueryOptimizationProfile(conn)
        self.pool_config = ConnectionPoolConfig()
        self.lazy_loader = LazyLoader(conn)
        self.pagination = PaginationHelper(conn)

    def optimize_indexes(self) -> Dict[str, Any]:
        """
        Create all recommended indexes.

        Returns:
            Dictionary with index creation results
        """
        return {
            "action": "Index Optimization",
            "results": self.index_registry.create_all_indexes(self.conn),
            "recommendations": self.index_registry.get_index_recommendations()
        }

    def analyze_performance(self) -> Dict[str, Any]:
        """
        Analyze database performance and get recommendations.

        Returns:
            Dictionary with performance analysis
        """
        return {
            "action": "Performance Analysis",
            "index_coverage": self.query_profile.get_index_coverage(),
            "recommendations": self.query_profile.get_recommendations(),
            "pool_stats": self.pool_config.get_stats()
        }

    def get_optimization_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive optimization report.

        Returns:
            Complete optimization report
        """
        return {
            "timestamp": str(__import__('datetime').datetime.now()),
            "index_optimization": self.optimize_indexes(),
            "performance_analysis": self.analyze_performance(),
            "pool_configuration": self.pool_config.get_stats(),
            "index_registry": self.index_registry.get_index_recommendations()
        }


# Convenience functions for integration with existing Database class

def optimize_existing_database(db_instance) -> Dict[str, Any]:
    """
    Optimize an existing Database instance.

    Args:
        db_instance: Instance of Database class from db.py

    Returns:
        Optimization report
    """
    with db_instance.pool.get_connection(write=True) as conn:
        optimizer = DatabaseOptimizer(conn)
        return optimizer.get_optimization_report()


def apply_optimization_pragmas(db_instance) -> None:
    """
    Apply optimization pragmas to database connection pool.

    Args:
        db_instance: Instance of Database class from db.py
    """
    pool_config = ConnectionPoolConfig()
    with db_instance.pool.get_connection(write=False) as conn:
        pool_config.apply_pragmas(conn)
    logger.info("Optimization pragmas applied")


def get_pagination_helper(db_instance) -> PaginationHelper:
    """
    Get pagination helper for database instance.

    Args:
        db_instance: Instance of Database class from db.py

    Returns:
        PaginationHelper instance
    """
    with db_instance.pool.get_connection(write=False) as conn:
        return PaginationHelper(conn)


def get_lazy_loader(db_instance, batch_size: int = 1000) -> LazyLoader:
    """
    Get lazy loader for database instance.

    Args:
        db_instance: Instance of Database class from db.py
        batch_size: Batch size for lazy loading

    Returns:
        LazyLoader instance
    """
    with db_instance.pool.get_connection(write=False) as conn:
        return LazyLoader(conn, batch_size)
