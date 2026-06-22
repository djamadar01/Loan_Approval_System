"""
Example usage of the monitoring module with a complete Flask application.
Demonstrates all monitoring features and best practices.
"""

import time
import random
from flask import Flask, jsonify, request
from monitoring import (
    setup_monitoring,
    track_decision,
    track_errors,
    DecisionTimer,
    MonitoringConfig
)


def create_app():
    """Create and configure Flask app with monitoring."""
    app = Flask(__name__)

    # Set up comprehensive monitoring
    logger, metrics, error_tracker, health_checker = setup_monitoring(app)

    # Store components in app extensions for decorator access
    app.extensions['monitoring_logger'] = logger
    app.extensions['monitoring_metrics'] = metrics
    app.extensions['monitoring_error_tracker'] = error_tracker
    app.extensions['monitoring_health_checker'] = health_checker

    # ========================================================================
    # Example Routes
    # ========================================================================

    @app.route("/")
    def index():
        """Root endpoint."""
        logger.info("Index endpoint accessed")
        return jsonify({
            "status": "running",
            "service": "Monitoring Example App",
            "endpoints": {
                "health": "/health",
                "metrics": "/metrics",
                "errors": "/api/errors",
                "api/users": "/api/users",
                "api/users/<id>": "/api/users/<id>",
                "api/decision": "/api/decision",
                "api/process": "/api/process"
            }
        })

    # ========================================================================
    # Example: User Management (Basic CRUD with logging)
    # ========================================================================

    users_db = {
        1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
        2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
    }
    next_user_id = 3

    @app.route("/api/users", methods=["GET"])
    def list_users():
        """List all users."""
        logger.info("Listing users", user_count=len(users_db))
        return jsonify({
            "users": list(users_db.values()),
            "count": len(users_db)
        })

    @app.route("/api/users", methods=["POST"])
    @track_errors
    def create_user():
        """Create a new user."""
        nonlocal next_user_id

        data = request.get_json()

        if not data or 'name' not in data:
            logger.warning("Invalid user creation request", data=data)
            return jsonify({"error": "Missing required fields"}), 400

        new_user = {
            "id": next_user_id,
            "name": data['name'],
            "email": data.get('email', '')
        }

        users_db[next_user_id] = new_user
        next_user_id += 1

        logger.info(
            "User created",
            user_id=new_user['id'],
            user_name=new_user['name']
        )

        return jsonify(new_user), 201

    @app.route("/api/users/<int:user_id>", methods=["GET"])
    @track_errors
    def get_user(user_id):
        """Get specific user."""
        if user_id not in users_db:
            logger.warning(f"User not found", user_id=user_id)
            return jsonify({"error": "User not found"}), 404

        logger.info(f"User retrieved", user_id=user_id)
        return jsonify(users_db[user_id])

    @app.route("/api/users/<int:user_id>", methods=["PUT"])
    @track_errors
    def update_user(user_id):
        """Update user."""
        if user_id not in users_db:
            logger.warning(f"User not found for update", user_id=user_id)
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        users_db[user_id].update(data)

        logger.info(f"User updated", user_id=user_id, changes=data)
        return jsonify(users_db[user_id])

    @app.route("/api/users/<int:user_id>", methods=["DELETE"])
    @track_errors
    def delete_user(user_id):
        """Delete user."""
        if user_id not in users_db:
            logger.warning(f"User not found for deletion", user_id=user_id)
            return jsonify({"error": "User not found"}), 404

        deleted_user = users_db.pop(user_id)
        logger.info(f"User deleted", user_id=user_id, user_name=deleted_user['name'])
        return jsonify({"deleted": deleted_user})

    # ========================================================================
    # Example: Decision Processing with Timing
    # ========================================================================

    @app.route("/api/decision", methods=["POST"])
    @track_decision("recommendation_engine")
    def make_recommendation():
        """Make a recommendation based on input data."""
        data = request.get_json() or {}

        # Simulate decision processing
        processing_time = random.uniform(0.1, 0.8)
        time.sleep(processing_time)

        recommendation = {
            "input": data,
            "recommendation": f"Recommended action based on {data}",
            "confidence": random.uniform(0.7, 0.99),
            "processing_time": processing_time
        }

        logger.info(
            "Recommendation made",
            confidence=recommendation['confidence'],
            processing_time=processing_time
        )

        return jsonify(recommendation)

    # ========================================================================
    # Example: Complex Processing with Custom Timing
    # ========================================================================

    @app.route("/api/process", methods=["POST"])
    @track_errors
    def process_data():
        """Process data with multiple decision points."""
        data = request.get_json() or {}

        # Track overall processing
        with DecisionTimer(metrics, "data_processing", logger):
            # Decision 1: Validation
            with DecisionTimer(metrics, "validation", logger):
                time.sleep(0.05)
                logger.debug("Data validation", data_size=len(str(data)))

            # Decision 2: Transformation
            with DecisionTimer(metrics, "transformation", logger):
                time.sleep(0.1)
                logger.debug("Data transformation")

            # Decision 3: Storage
            with DecisionTimer(metrics, "storage", logger):
                time.sleep(0.08)
                logger.debug("Data storage")

            result = {
                "status": "processed",
                "data_size": len(str(data)),
                "timestamp": time.time()
            }

            logger.info("Data processing completed", result=result)
            return jsonify(result)

    # ========================================================================
    # Example: Error Simulation
    # ========================================================================

    @app.route("/api/error/simulate", methods=["POST"])
    @track_errors
    def simulate_error():
        """Simulate an error."""
        error_type = request.args.get("type", "value_error")

        logger.warning(f"Simulating error: {error_type}")

        if error_type == "value_error":
            raise ValueError("Simulated value error for testing")
        elif error_type == "key_error":
            raise KeyError("Simulated key error for testing")
        elif error_type == "runtime_error":
            raise RuntimeError("Simulated runtime error for testing")
        else:
            raise Exception(f"Unknown error type: {error_type}")

    # ========================================================================
    # Example: Stress Testing (generates multiple errors)
    # ========================================================================

    @app.route("/api/stress", methods=["POST"])
    def stress_test():
        """Stress test endpoint to generate errors."""
        iterations = request.args.get("iterations", default=5, type=int)

        logger.info(f"Starting stress test with {iterations} iterations")

        errors = []
        for i in range(iterations):
            try:
                # Randomly fail requests
                if random.random() < 0.3:
                    raise Exception(f"Stress test error {i}")

                # Random processing
                time.sleep(random.uniform(0.01, 0.2))

                metrics.record_request(
                    method="GET",
                    endpoint="/api/stress",
                    status_code=200,
                    duration=0.05
                )
            except Exception as e:
                errors.append(str(e))
                error_tracker.record_error(
                    error_type="StressTestError",
                    error_message=str(e),
                    traceback=str(e)
                )

        logger.info(
            f"Stress test completed",
            iterations=iterations,
            errors=len(errors)
        )

        return jsonify({
            "iterations": iterations,
            "errors": len(errors),
            "error_list": errors
        })

    # ========================================================================
    # Example: Slow Request (for monitoring)
    # ========================================================================

    @app.route("/api/slow", methods=["GET"])
    def slow_endpoint():
        """Endpoint that takes a long time (to test slow request detection)."""
        duration = request.args.get("duration", default=2.0, type=float)
        logger.info(f"Slow endpoint called, sleeping for {duration}s")
        time.sleep(duration)
        return jsonify({
            "message": "Completed slow request",
            "duration": duration
        })

    # ========================================================================
    # Example: Statistics and Monitoring
    # ========================================================================

    @app.route("/api/stats", methods=["GET"])
    def get_statistics():
        """Get application statistics."""
        health_data = health_checker.check_health()
        error_stats = error_tracker.get_error_stats()

        stats = {
            "health": health_data,
            "errors": error_stats,
            "endpoints": {
                "health": f"http://localhost:5000{MonitoringConfig.HEALTH_CHECK_ENDPOINT}",
                "metrics": f"http://localhost:5000{MonitoringConfig.METRICS_ENDPOINT}",
                "errors": f"http://localhost:5000/api/errors"
            }
        }

        logger.info("Statistics retrieved")
        return jsonify(stats)

    logger.info("Application setup complete with all monitoring endpoints")

    return app


if __name__ == "__main__":
    app = create_app()
    print("""
    ========================================================================
    Monitoring Example App Started
    ========================================================================

    Available Endpoints:
    - GET  http://localhost:5000/                 (Info)
    - GET  http://localhost:5000/health            (Health Check)
    - GET  http://localhost:5000/metrics           (Prometheus Metrics)
    - GET  http://localhost:5000/api/errors        (Error Logs)
    - GET  http://localhost:5000/api/stats         (Statistics)

    User Management:
    - GET  http://localhost:5000/api/users         (List Users)
    - POST http://localhost:5000/api/users         (Create User)
    - GET  http://localhost:5000/api/users/<id>    (Get User)
    - PUT  http://localhost:5000/api/users/<id>    (Update User)
    - DELETE http://localhost:5000/api/users/<id>  (Delete User)

    Decision Processing:
    - POST http://localhost:5000/api/decision      (Make Decision)
    - POST http://localhost:5000/api/process       (Process Data)

    Testing:
    - POST http://localhost:5000/api/error/simulate?type=value_error
    - POST http://localhost:5000/api/stress?iterations=10
    - GET  http://localhost:5000/api/slow?duration=2

    Log Files:
    - ./logs/app.log        (Text format)
    - ./logs/app.json.log   (JSON format)
    - ./logs/errors.log     (Errors only)

    ========================================================================
    """)

    app.run(debug=False, host="0.0.0.0", port=5000)
