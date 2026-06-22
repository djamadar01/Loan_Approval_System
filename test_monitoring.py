"""
Test script for monitoring module.
Demonstrates all monitoring features and validates functionality.
"""

import json
import time
import requests
from pathlib import Path
from monitoring_example import create_app
from threading import Thread


class MonitoringTester:
    """Test suite for monitoring functionality."""

    def __init__(self, base_url="http://localhost:5000"):
        """Initialize tester."""
        self.base_url = base_url
        self.results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": []
        }

    def test_basic_endpoints(self):
        """Test basic endpoints."""
        print("\n=== Testing Basic Endpoints ===")

        # Test root endpoint
        print("Testing GET /")
        try:
            response = requests.get(f"{self.base_url}/")
            assert response.status_code == 200
            assert "status" in response.json()
            print("✓ Root endpoint works")
            self._record_pass("Root endpoint")
        except Exception as e:
            print(f"✗ Root endpoint failed: {e}")
            self._record_fail("Root endpoint", str(e))

    def test_health_check(self):
        """Test health check endpoint."""
        print("\n=== Testing Health Check ===")

        try:
            response = requests.get(f"{self.base_url}/health")
            assert response.status_code in [200, 503]
            health_data = response.json()
            assert "status" in health_data
            assert "cpu_percent" in health_data
            assert "memory_percent" in health_data
            assert "errors" in health_data
            print(f"✓ Health check works - Status: {health_data['status']}")
            print(f"  CPU: {health_data['cpu_percent']:.1f}%")
            print(f"  Memory: {health_data['memory_percent']:.1f}%")
            print(f"  Uptime: {health_data['uptime_seconds']:.1f}s")
            self._record_pass("Health check")
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            self._record_fail("Health check", str(e))

    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""
        print("\n=== Testing Metrics Endpoint ===")

        try:
            response = requests.get(f"{self.base_url}/metrics")
            assert response.status_code == 200
            metrics_text = response.text

            # Check for key metrics
            assert "requests_total" in metrics_text
            assert "request_duration_seconds" in metrics_text
            assert "errors_total" in metrics_text
            assert "cpu_usage_percent" in metrics_text

            print("✓ Metrics endpoint works")
            print(f"  Response size: {len(metrics_text)} bytes")
            print(f"  Sample metrics found:")
            for line in metrics_text.split('\n'):
                if line and not line.startswith('#') and any(
                    metric in line for metric in ['requests_total', 'cpu_usage', 'memory_usage']
                ):
                    print(f"    {line}")

            self._record_pass("Metrics endpoint")
        except Exception as e:
            print(f"✗ Metrics endpoint failed: {e}")
            self._record_fail("Metrics endpoint", str(e))

    def test_user_management(self):
        """Test user management endpoints."""
        print("\n=== Testing User Management ===")

        try:
            # Get users
            response = requests.get(f"{self.base_url}/api/users")
            assert response.status_code == 200
            initial_count = response.json()["count"]
            print(f"✓ Got users list ({initial_count} users)")

            # Create user
            new_user = {
                "name": "Test User",
                "email": "test@example.com"
            }
            response = requests.post(
                f"{self.base_url}/api/users",
                json=new_user
            )
            assert response.status_code == 201
            created_user = response.json()
            user_id = created_user["id"]
            print(f"✓ Created user (ID: {user_id})")

            # Get user
            response = requests.get(f"{self.base_url}/api/users/{user_id}")
            assert response.status_code == 200
            print(f"✓ Retrieved user")

            # Update user
            update_data = {"email": "updated@example.com"}
            response = requests.put(
                f"{self.base_url}/api/users/{user_id}",
                json=update_data
            )
            assert response.status_code == 200
            print(f"✓ Updated user")

            # Delete user
            response = requests.delete(f"{self.base_url}/api/users/{user_id}")
            assert response.status_code == 200
            print(f"✓ Deleted user")

            self._record_pass("User management")
        except Exception as e:
            print(f"✗ User management failed: {e}")
            self._record_fail("User management", str(e))

    def test_decision_processing(self):
        """Test decision processing with timing."""
        print("\n=== Testing Decision Processing ===")

        try:
            response = requests.post(
                f"{self.base_url}/api/decision",
                json={"user_id": 1, "criteria": "test"}
            )
            assert response.status_code == 200
            result = response.json()
            assert "recommendation" in result
            assert "confidence" in result
            assert "processing_time" in result

            print(f"✓ Decision processed")
            print(f"  Confidence: {result['confidence']:.2%}")
            print(f"  Processing time: {result['processing_time']:.3f}s")

            self._record_pass("Decision processing")
        except Exception as e:
            print(f"✗ Decision processing failed: {e}")
            self._record_fail("Decision processing", str(e))

    def test_complex_processing(self):
        """Test complex data processing with multiple decision points."""
        print("\n=== Testing Complex Processing ===")

        try:
            response = requests.post(
                f"{self.base_url}/api/process",
                json={"data": "test", "items": [1, 2, 3]}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "processed"

            print(f"✓ Complex processing completed")
            print(f"  Data size: {result['data_size']} bytes")

            self._record_pass("Complex processing")
        except Exception as e:
            print(f"✗ Complex processing failed: {e}")
            self._record_fail("Complex processing", str(e))

    def test_error_tracking(self):
        """Test error tracking functionality."""
        print("\n=== Testing Error Tracking ===")

        try:
            # Trigger a ValueError
            response = requests.post(
                f"{self.base_url}/api/error/simulate?type=value_error"
            )
            assert response.status_code == 500
            print("✓ ValueError triggered and caught")

            # Trigger a KeyError
            response = requests.post(
                f"{self.base_url}/api/error/simulate?type=key_error"
            )
            assert response.status_code == 500
            print("✓ KeyError triggered and caught")

            # Check error logs
            time.sleep(0.5)  # Give time for logging
            response = requests.get(f"{self.base_url}/api/errors?limit=10")
            assert response.status_code == 200
            errors_data = response.json()
            assert len(errors_data["errors"]) > 0
            assert "stats" in errors_data

            print(f"✓ Error tracking works")
            print(f"  Total errors recorded: {errors_data['stats']['total_errors']}")
            print(f"  Errors by type: {errors_data['stats']['errors_by_type']}")

            self._record_pass("Error tracking")
        except Exception as e:
            print(f"✗ Error tracking failed: {e}")
            self._record_fail("Error tracking", str(e))

    def test_log_files(self):
        """Test log file creation and content."""
        print("\n=== Testing Log Files ===")

        try:
            # Check log files exist
            log_dir = Path("./logs")
            assert log_dir.exists(), "Logs directory not found"
            print(f"✓ Logs directory exists")

            # Check text log
            text_log = log_dir / "app.log"
            assert text_log.exists(), "Text log file not found"
            text_content = text_log.read_text()
            assert len(text_content) > 0
            print(f"✓ Text log file created ({len(text_content)} bytes)")

            # Check JSON log
            json_log = log_dir / "app.json.log"
            assert json_log.exists(), "JSON log file not found"
            json_content = json_log.read_text()
            assert len(json_content) > 0

            # Verify JSON format
            lines = json_content.strip().split('\n')
            json_records = 0
            for line in lines:
                if line:
                    try:
                        json.loads(line)
                        json_records += 1
                    except:
                        pass

            print(f"✓ JSON log file created ({len(json_content)} bytes, {json_records} records)")

            # Show sample log entries
            if json_records > 0:
                sample_record = json.loads(lines[0])
                print(f"  Sample record: {json.dumps(sample_record, indent=2)}")

            self._record_pass("Log files")
        except Exception as e:
            print(f"✗ Log files test failed: {e}")
            self._record_fail("Log files", str(e))

    def test_slow_requests(self):
        """Test slow request detection."""
        print("\n=== Testing Slow Request Detection ===")

        try:
            # Make a slow request
            start = time.time()
            response = requests.get(
                f"{self.base_url}/api/slow?duration=0.5"
            )
            duration = time.time() - start

            assert response.status_code == 200
            print(f"✓ Slow request completed ({duration:.2f}s)")

            # Check metrics
            response = requests.get(f"{self.base_url}/metrics")
            assert "slow_requests_total" in response.text
            print(f"✓ Slow request tracking available in metrics")

            self._record_pass("Slow request detection")
        except Exception as e:
            print(f"✗ Slow request detection failed: {e}")
            self._record_fail("Slow request detection", str(e))

    def test_statistics(self):
        """Test statistics endpoint."""
        print("\n=== Testing Statistics ===")

        try:
            response = requests.get(f"{self.base_url}/api/stats")
            assert response.status_code == 200
            stats = response.json()

            assert "health" in stats
            assert "errors" in stats
            assert "endpoints" in stats

            print(f"✓ Statistics endpoint works")
            print(f"  Health status: {stats['health']['status']}")
            print(f"  Total errors: {stats['errors']['total_errors']}")

            self._record_pass("Statistics")
        except Exception as e:
            print(f"✗ Statistics test failed: {e}")
            self._record_fail("Statistics", str(e))

    def test_stress(self):
        """Test stress test functionality."""
        print("\n=== Testing Stress Test ===")

        try:
            response = requests.post(
                f"{self.base_url}/api/stress?iterations=5"
            )
            assert response.status_code == 200
            result = response.json()
            assert result["iterations"] == 5

            print(f"✓ Stress test completed")
            print(f"  Iterations: {result['iterations']}")
            print(f"  Errors: {result['errors']}")

            self._record_pass("Stress test")
        except Exception as e:
            print(f"✗ Stress test failed: {e}")
            self._record_fail("Stress test", str(e))

    def run_all_tests(self):
        """Run all tests."""
        print("\n" + "=" * 60)
        print("MONITORING MODULE TEST SUITE")
        print("=" * 60)

        try:
            # Wait for server startup
            print("\nWaiting for server to be ready...")
            for i in range(10):
                try:
                    requests.get(f"{self.base_url}/")
                    break
                except:
                    if i == 9:
                        raise
                    time.sleep(0.5)

            # Run tests
            self.test_basic_endpoints()
            self.test_health_check()
            self.test_metrics_endpoint()
            self.test_user_management()
            self.test_decision_processing()
            self.test_complex_processing()
            self.test_error_tracking()
            self.test_log_files()
            self.test_slow_requests()
            self.test_statistics()
            self.test_stress()

        except Exception as e:
            print(f"\n✗ Test suite failed to start: {e}")
            self.results["tests_failed"] += 1

        # Print summary
        self._print_summary()

    def _record_pass(self, test_name):
        """Record passing test."""
        self.results["tests_passed"] += 1
        self.results["test_details"].append({
            "test": test_name,
            "status": "PASSED"
        })

    def _record_fail(self, test_name, error):
        """Record failing test."""
        self.results["tests_failed"] += 1
        self.results["test_details"].append({
            "test": test_name,
            "status": "FAILED",
            "error": error
        })

    def _print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"✓ Passed: {self.results['tests_passed']}")
        print(f"✗ Failed: {self.results['tests_failed']}")
        total = self.results['tests_passed'] + self.results['tests_failed']
        if total > 0:
            percentage = (self.results['tests_passed'] / total) * 100
            print(f"Success Rate: {percentage:.1f}%")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    # Create and run app in background
    app = create_app()

    def run_app():
        app.run(debug=False, use_reloader=False, host="0.0.0.0", port=5000)

    app_thread = Thread(target=run_app, daemon=True)
    app_thread.start()

    # Run tests
    time.sleep(2)  # Give server time to start
    tester = MonitoringTester()
    tester.run_all_tests()
