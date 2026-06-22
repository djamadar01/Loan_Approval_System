"""
Test suite for database optimization module.

Validates that all optimization features work correctly with the existing db.py
"""

import unittest
import tempfile
import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime

from db import Database, ApplicationRecord, get_db
from db_optimization import (
    DatabaseOptimizer,
    IndexOptimizationRegistry,
    QueryOptimizationProfile,
    ConnectionPoolConfig,
    LazyLoader,
    PaginationHelper,
    optimize_existing_database,
    apply_optimization_pragmas,
)


class TestIndexOptimization(unittest.TestCase):
    """Test index optimization features."""

    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(db_dir=self.temp_dir, pool_size=3)

    def tearDown(self):
        """Clean up test database."""
        self.db.close()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_index_registry_initialization(self):
        """Test that index registry initializes with default indexes."""
        registry = IndexOptimizationRegistry()
        indexes = registry.get_all_indexes()

        self.assertGreater(len(indexes), 0)
        self.assertTrue(any(idx.name == "idx_applications_status" for idx in indexes))
        self.assertTrue(any(idx.name == "idx_applications_company" for idx in indexes))

    def test_index_creation(self):
        """Test that indexes can be created successfully."""
        with self.db.pool.get_connection(write=True) as conn:
            registry = IndexOptimizationRegistry()
            results = registry.create_all_indexes(conn)

            # All indexes should be created successfully
            self.assertTrue(all(results.values()))

    def test_get_indexes_for_table(self):
        """Test retrieving indexes for specific table."""
        registry = IndexOptimizationRegistry()
        app_indexes = registry.get_indexes_for_table("applications")

        self.assertGreater(len(app_indexes), 0)
        for idx in app_indexes:
            self.assertEqual(idx.table, "applications")


class TestQueryOptimization(unittest.TestCase):
    """Test query optimization features."""

    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(db_dir=self.temp_dir)
        self._add_test_data()

    def tearDown(self):
        """Clean up test database."""
        self.db.close()
        import shutil
        shutil.rmtree(self.temp_dir)

    def _add_test_data(self):
        """Add test data to database."""
        for i in range(10):
            record = ApplicationRecord(
                job_title=f"Engineer {i}",
                company_name=f"Company {i % 3}",
                status="applied" if i % 2 == 0 else "interview",
                match_score=70 + i,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            self.db.create_application(record)

    def test_query_analysis(self):
        """Test that query analysis works."""
        with self.db.pool.get_connection() as conn:
            profile = QueryOptimizationProfile(conn)
            analysis = profile.analyze_query(
                "SELECT * FROM applications WHERE status = ?",
                ["applied"]
            )

            self.assertIn("query", analysis)
            self.assertIn("plan", analysis)
            self.assertIn("recommendations", analysis)

    def test_index_coverage(self):
        """Test index coverage report."""
        with self.db.pool.get_connection() as conn:
            profile = QueryOptimizationProfile(conn)
            coverage = profile.get_index_coverage()

            self.assertIn("total_indexes", coverage)
            self.assertIn("by_table", coverage)
            self.assertGreater(coverage["total_indexes"], 0)

    def test_recommendations(self):
        """Test that recommendations are generated."""
        with self.db.pool.get_connection() as conn:
            profile = QueryOptimizationProfile(conn)
            recommendations = profile.get_recommendations()

            self.assertIsInstance(recommendations, list)


class TestConnectionPooling(unittest.TestCase):
    """Test connection pool configuration."""

    def test_pool_config_initialization(self):
        """Test pool configuration initializes correctly."""
        config = ConnectionPoolConfig()

        self.assertEqual(config.settings.pool_size, 5)
        self.assertGreater(config.settings.cache_size, 0)
        self.assertEqual(config.settings.journal_mode, "WAL")

    def test_optimized_pragmas(self):
        """Test that optimized pragmas are returned."""
        config = ConnectionPoolConfig()
        pragmas = config.get_optimized_pragmas()

        self.assertGreater(len(pragmas), 0)
        pragma_names = [p[0] for p in pragmas]
        self.assertIn("PRAGMA journal_mode", pragma_names)
        self.assertIn("PRAGMA synchronous", pragma_names)

    def test_connection_stats(self):
        """Test connection statistics tracking."""
        config = ConnectionPoolConfig()

        config.record_acquisition()
        self.assertEqual(config.connection_stats["total_acquired"], 1)

        config.record_query(150)
        self.assertEqual(config.connection_stats["total_queries"], 1)

        config.record_release()
        self.assertEqual(config.connection_stats["total_released"], 1)


class TestLazyLoading(unittest.TestCase):
    """Test lazy loading features."""

    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(db_dir=self.temp_dir)
        self._add_test_data()

    def tearDown(self):
        """Clean up test database."""
        self.db.close()
        import shutil
        shutil.rmtree(self.temp_dir)

    def _add_test_data(self):
        """Add test data to database."""
        for i in range(50):
            record = ApplicationRecord(
                job_title=f"Position {i}",
                company_name=f"Company {i % 5}",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            self.db.create_application(record)

    def test_lazy_query_batches(self):
        """Test lazy loading with batches."""
        with self.db.pool.get_connection() as conn:
            loader = LazyLoader(conn, batch_size=10)

            batches = list(loader.lazy_query("SELECT * FROM applications"))
            total_rows = sum(len(batch) for batch in batches)

            self.assertEqual(total_rows, 50)
            self.assertLessEqual(len(batches[0]), 10)

    def test_lazy_iterator(self):
        """Test lazy loading with iterator."""
        with self.db.pool.get_connection() as conn:
            loader = LazyLoader(conn)
            rows = list(loader.lazy_iterator("SELECT * FROM applications"))

            self.assertEqual(len(rows), 50)

    def test_stream_to_file(self):
        """Test streaming to file."""
        with self.db.pool.get_connection() as conn:
            loader = LazyLoader(conn)
            output_file = os.path.join(self.temp_dir, "export.txt")

            count = loader.stream_to_file(
                "SELECT * FROM applications",
                output_file,
                format_func=lambda r: f"{r['company_name']}: {r['job_title']}"
            )

            self.assertEqual(count, 50)
            self.assertTrue(os.path.exists(output_file))
            with open(output_file) as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 50)


class TestPagination(unittest.TestCase):
    """Test pagination features."""

    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(db_dir=self.temp_dir)
        self._add_test_data()

    def tearDown(self):
        """Clean up test database."""
        self.db.close()
        import shutil
        shutil.rmtree(self.temp_dir)

    def _add_test_data(self):
        """Add test data to database."""
        for i in range(100):
            record = ApplicationRecord(
                job_title=f"Position {i}",
                company_name=f"Company {i % 5}",
                status="applied" if i % 2 == 0 else "interview",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            self.db.create_application(record)

    def test_offset_pagination(self):
        """Test offset-based pagination."""
        with self.db.pool.get_connection() as conn:
            helper = PaginationHelper(conn)

            page1 = helper.paginate(
                query="SELECT * FROM applications",
                count_query="SELECT COUNT(*) FROM applications",
                params=[],
                page=1,
                page_size=20
            )

            self.assertEqual(page1.page_number, 1)
            self.assertEqual(len(page1.items), 20)
            self.assertEqual(page1.total_count, 100)
            self.assertEqual(page1.total_pages, 5)
            self.assertTrue(page1.has_next)
            self.assertFalse(page1.has_previous)

    def test_filtered_pagination(self):
        """Test pagination with filters."""
        with self.db.pool.get_connection() as conn:
            helper = PaginationHelper(conn)

            page = helper.paginate(
                query="SELECT * FROM applications WHERE status = ?",
                count_query="SELECT COUNT(*) FROM applications WHERE status = ?",
                params=["interview"],
                page=1,
                page_size=10
            )

            self.assertLessEqual(len(page.items), 50)
            self.assertLessEqual(page.total_count, 100)

    def test_cursor_pagination(self):
        """Test cursor-based pagination."""
        with self.db.pool.get_connection() as conn:
            helper = PaginationHelper(conn)

            page1 = helper.cursor_paginate(
                query="SELECT * FROM applications WHERE 1=1",
                params=[],
                cursor_column="id",
                page_size=10
            )

            self.assertEqual(len(page1.items), 10)
            self.assertTrue(page1.has_next)
            self.assertFalse(page1.has_previous)

            if hasattr(page1, "next_cursor"):
                page2 = helper.cursor_paginate(
                    query="SELECT * FROM applications WHERE 1=1",
                    params=[],
                    cursor_column="id",
                    page_size=10,
                    after_cursor=page1.next_cursor
                )
                self.assertGreater(len(page2.items), 0)

    def test_pagination_info(self):
        """Test pagination info dictionary."""
        with self.db.pool.get_connection() as conn:
            helper = PaginationHelper(conn)

            page = helper.paginate(
                query="SELECT * FROM applications",
                count_query="SELECT COUNT(*) FROM applications",
                params=[],
                page=1,
                page_size=20
            )

            info = page.get_info()
            self.assertIn("page", info)
            self.assertIn("total_items", info)
            self.assertIn("total_pages", info)
            self.assertIn("has_next", info)
            self.assertIn("query_time_ms", info)


class TestDatabaseOptimizer(unittest.TestCase):
    """Test high-level database optimizer."""

    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(db_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test database."""
        self.db.close()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_optimizer_initialization(self):
        """Test optimizer initializes correctly."""
        with self.db.pool.get_connection() as conn:
            optimizer = DatabaseOptimizer(conn)

            self.assertIsNotNone(optimizer.index_registry)
            self.assertIsNotNone(optimizer.query_profile)
            self.assertIsNotNone(optimizer.pool_config)
            self.assertIsNotNone(optimizer.lazy_loader)
            self.assertIsNotNone(optimizer.pagination)

    def test_optimize_indexes(self):
        """Test index optimization."""
        with self.db.pool.get_connection(write=True) as conn:
            optimizer = DatabaseOptimizer(conn)
            result = optimizer.optimize_indexes()

            self.assertIn("results", result)
            self.assertIn("recommendations", result)
            # Most indexes should be created
            self.assertGreater(len(result["results"]), 0)

    def test_analyze_performance(self):
        """Test performance analysis."""
        with self.db.pool.get_connection() as conn:
            optimizer = DatabaseOptimizer(conn)
            result = optimizer.analyze_performance()

            self.assertIn("index_coverage", result)
            self.assertIn("recommendations", result)
            self.assertIn("pool_stats", result)

    def test_optimization_report(self):
        """Test complete optimization report."""
        with self.db.pool.get_connection(write=True) as conn:
            optimizer = DatabaseOptimizer(conn)
            report = optimizer.get_optimization_report()

            self.assertIn("timestamp", report)
            self.assertIn("index_optimization", report)
            self.assertIn("performance_analysis", report)
            self.assertIn("pool_configuration", report)


class TestIntegration(unittest.TestCase):
    """Test integration with existing db.py."""

    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(db_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test database."""
        self.db.close()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_optimize_existing_database(self):
        """Test optimize_existing_database function."""
        report = optimize_existing_database(self.db)

        self.assertIsInstance(report, dict)
        self.assertIn("index_optimization", report)
        self.assertIn("performance_analysis", report)

    def test_apply_optimization_pragmas(self):
        """Test apply_optimization_pragmas function."""
        # Should not raise any exceptions
        apply_optimization_pragmas(self.db)

    def test_backward_compatibility(self):
        """Test that existing db.py functions still work."""
        record = ApplicationRecord(
            job_title="Test",
            company_name="Test Co",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        # Original API should still work
        app_id = self.db.create_application(record)
        self.assertIsNotNone(app_id)

        retrieved = self.db.get_application(app_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.job_title, "Test")

        stats = self.db.get_statistics()
        self.assertEqual(stats["total_applications"], 1)


def run_tests():
    """Run all tests and generate report."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestIndexOptimization))
    suite.addTests(loader.loadTestsFromTestCase(TestQueryOptimization))
    suite.addTests(loader.loadTestsFromTestCase(TestConnectionPooling))
    suite.addTests(loader.loadTestsFromTestCase(TestLazyLoading))
    suite.addTests(loader.loadTestsFromTestCase(TestPagination))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseOptimizer))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
