#!/usr/bin/env python3
"""
Test script for temporal sequence learning.

Simulates a typical coding workflow and demonstrates sequence prediction.

Usage:
    python3 test_sequence_learning.py
"""

import redis
import time
import json
from sequence_tracker import SequenceTracker, format_prediction


def simulate_workflow(tracker: SequenceTracker, session_id: str):
    """
    Simulate a realistic coding workflow.

    Pattern: Test-Driven Development
    1. Edit test file
    2. Edit implementation
    3. Run tests
    4. Edit test file again
    5. Edit implementation again
    """
    print("=" * 60)
    print("Simulating Test-Driven Development Workflow")
    print("=" * 60)

    workflow = [
        ("/project/tests/test_auth.py", "Edit", 0),
        ("/project/src/auth.py", "Edit", 2),
        ("/project/tests/test_auth.py", "Read", 1),
        ("/project/src/auth.py", "Edit", 3),
        ("/project/tests/test_auth.py", "Edit", 2),
        ("/project/src/auth.py", "Edit", 1),
    ]

    for file_path, tool, delay in workflow:
        print(f"\n[{tool}] {file_path}")
        tracker.record_access(file_path, tool, session_id)
        time.sleep(delay)

    print("\n" + "=" * 60)
    print("Workflow complete. Learning patterns...")
    print("=" * 60)


def simulate_api_workflow(tracker: SequenceTracker, session_id: str):
    """
    Simulate API development workflow.

    Pattern: Route → Schema → Controller → Test
    """
    print("\n" + "=" * 60)
    print("Simulating API Development Workflow")
    print("=" * 60)

    workflow = [
        ("/project/routes/user.py", "Edit", 0),
        ("/project/schemas/user.py", "Edit", 2),
        ("/project/controllers/user.py", "Edit", 3),
        ("/project/tests/test_user.py", "Edit", 2),
        # Repeat pattern
        ("/project/routes/post.py", "Edit", 1),
        ("/project/schemas/post.py", "Edit", 2),
        ("/project/controllers/post.py", "Edit", 2),
        ("/project/tests/test_post.py", "Edit", 3),
    ]

    for file_path, tool, delay in workflow:
        print(f"\n[{tool}] {file_path}")
        tracker.record_access(file_path, tool, session_id)
        time.sleep(delay)

    print("\n" + "=" * 60)
    print("API workflow complete")
    print("=" * 60)


def test_predictions(tracker: SequenceTracker):
    """Test predictions after learning."""
    print("\n" + "=" * 60)
    print("Testing Predictions")
    print("=" * 60)

    test_cases = [
        "/project/tests/test_auth.py",
        "/project/src/auth.py",
        "/project/routes/user.py",
        "/project/schemas/user.py",
    ]

    for file_path in test_cases:
        print(f"\n📁 Current file: {file_path}")
        predictions = tracker.predict_next_files(file_path, limit=3)

        if predictions:
            print(format_prediction(predictions))
        else:
            print("  No predictions available yet")


def test_transition_matrix(tracker: SequenceTracker):
    """Display transition matrices."""
    print("\n" + "=" * 60)
    print("Transition Matrices")
    print("=" * 60)

    test_files = [
        "/project/tests/test_auth.py",
        "/project/src/auth.py",
        "/project/routes/user.py",
    ]

    for file_path in test_files:
        matrix = tracker.get_transition_matrix(file_path)
        if matrix:
            print(f"\n📊 {file_path}")
            for target, prob in sorted(matrix.items(), key=lambda x: x[1], reverse=True):
                print(f"  → {target}: {int(prob * 100)}%")


def test_session_predictions(tracker: SequenceTracker, session_id: str):
    """Test session-based predictions."""
    print("\n" + "=" * 60)
    print("Session-Based Predictions")
    print("=" * 60)

    predictions = tracker.predict_from_recent(session_id, limit=5)

    if predictions:
        print("\n🔮 Predicted next files based on recent activity:")
        print(format_prediction(predictions))
    else:
        print("  No session predictions available")


def display_stats(tracker: SequenceTracker):
    """Display learning statistics."""
    print("\n" + "=" * 60)
    print("Learning Statistics")
    print("=" * 60)

    stats = tracker.get_sequence_stats()

    print(f"\n📊 Total source files: {stats['total_source_files']}")
    print(f"📊 Total transitions: {stats['total_transitions']}")
    print(f"📊 Avg transitions per file: {stats['avg_transitions_per_file']:.1f}")


def main():
    """Run the test suite."""
    print("\n" + "=" * 60)
    print("🧪 Temporal Sequence Learning Test Suite")
    print("=" * 60)

    # Connect to Redis
    try:
        r = redis.from_url('redis://localhost:6379/0', decode_responses=True)
        r.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print("   Make sure Redis is running: redis-server")
        return

    # Initialize tracker
    project_id = "test-project"
    tracker = SequenceTracker(r, project_id)
    print(f"✅ Initialized sequence tracker for project: {project_id}")

    # Clean up old test data
    pattern = f"*{project_id}*"
    for key in r.scan_iter(match=pattern):
        r.delete(key)
    print("✅ Cleaned up old test data\n")

    # Run simulations
    session1 = "test-session-1"
    session2 = "test-session-2"

    # Simulate workflows
    simulate_workflow(tracker, session1)
    time.sleep(1)
    simulate_api_workflow(tracker, session2)

    # Test predictions
    time.sleep(1)
    test_predictions(tracker)

    # Test transition matrices
    test_transition_matrix(tracker)

    # Test session predictions
    test_session_predictions(tracker, session2)

    # Display stats
    display_stats(tracker)

    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Start the status service: python3 services/status/status_service.py")
    print("  2. Try the API endpoints:")
    print("     curl 'http://localhost:9998/sequence/stats?project_id=test-project'")
    print("     curl 'http://localhost:9998/sequence/predict?file=/project/src/auth.py&project_id=test-project'")
    print()


if __name__ == "__main__":
    main()
