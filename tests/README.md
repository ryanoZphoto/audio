# Test Documentation

## Overview
This directory contains all test files for the AudioSnipt application. The tests ensure that all core functionality works as expected.

## Test Structure
- `test_subscription_monitor.py`: Tests for subscription management system
  - Checks subscription expiration
  - Tests notification system
  - Validates subscription health monitoring
  - Verifies multiple subscription handling

## How to Run Tests

### Run All Tests
```bash
pytest -v
```

### Run Specific Test File
```bash
pytest tests/test_subscription_monitor.py -v
```

### Run a Specific Test
```bash
pytest tests/test_subscription_monitor.py -v -k "test_cleanup_expired_subscriptions"
```

## Test Output Explanation
- ✓ PASSED: Test completed successfully
- ⨯ FAILED: Test failed (will show error details)
- s SKIPPED: Test was skipped
- ! ERROR: Error occurred during test setup

## Common Issues
1. Database Connection Errors
   - Make sure the test database URL is correctly set
   - Verify database is running

2. Cache Errors
   - Ensure Redis is running for cache tests
   - Check Redis connection settings

3. Email Test Failures
   - Email tests use mocking, no real emails are sent
   - Verify email templates exist

## Adding New Tests
1. Create test file in this directory
2. Use appropriate fixtures from `conftest.py`
3. Follow existing test patterns
4. Add documentation to this README 