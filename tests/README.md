# Python IDE Test Suite

## Overview
This directory contains tests for the Python IDE system, focusing on security features and resource protection.

## Test Files

### `test_simple_exec_v3.py`
Unit tests for the SimpleExecutorV3 execution engine, covering:
- **Timeout Protection**: 3-second execution limit
- **Output Rate Limiting**: 100 lines/sec maximum
- **Identical Line Detection**: 500 repeats maximum
- **Total Output Limiting**: 10,000 lines maximum
- **REPL Functionality**: Interactive mode testing
- **Input Handling**: Testing `input()` function
- **Resource Cleanup**: Proper cleanup on stop

### `performance_test.py`
Performance testing script for concurrent users:
- WebSocket connection testing
- Multiple student simulation
- Load testing capabilities
- Response time measurement

### `load_test_50_students.py`
Load testing for 50+ concurrent students:
- Concurrent execution testing
- Resource usage monitoring
- System stability under load

## Running Tests

### Local Testing
```bash
# Run all unit tests
cd tests
python -m pytest test_simple_exec_v3.py -v

# Run with coverage
python -m pytest test_simple_exec_v3.py --cov=server/command --cov-report=html

# Run performance tests
python performance_test.py --students 10 --duration 30

# Run load test
python load_test_50_students.py
```

### CI/CD Testing
Tests run automatically via GitHub Actions on:
- Push to any branch (except main)
- Pull requests to main
- Manual workflow dispatch

## Safety Features Tested

### 1. Timeout Protection (3 seconds)
- Scripts automatically terminate after 3 seconds
- Prevents infinite loops from consuming resources
- Tested with various loop types

### 2. Output Rate Limiting (100 lines/sec)
- Prevents output flooding attacks
- Automatically kills processes exceeding rate
- Tested with rapid print loops

### 3. Identical Line Detection (500 repeats)
- Detects and stops repetitive output
- Prevents memory exhaustion from identical lines
- Tested with repetitive print statements

### 4. Total Output Limiting (10,000 lines)
- Absolute limit on total output
- Prevents memory exhaustion
- Tested with large output generation

### 5. Auto-Stop on Errors
- Console automatically stops on timeout
- Resources freed without manual intervention
- WebSocket properly cleaned up

## Test Requirements

```txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-timeout>=2.1.0
pytest-cov>=4.0.0
aiohttp>=3.8.0
```

## Security Considerations

All tests are designed to verify:
- No infinite loops can crash the system
- Memory usage is bounded
- CPU usage is limited
- Resources are properly freed
- No zombie processes remain

## Adding New Tests

When adding tests, ensure they:
1. Don't require actual database connections
2. Mock external dependencies properly
3. Clean up any temporary files
4. Are idempotent (can run multiple times)
5. Have clear assertions and error messages

## GitHub Actions Integration

Tests run in CI/CD pipeline with:
- Python 3.11
- Ubuntu latest
- Docker build verification
- Security scanning (Bandit, Safety)
- Code quality checks (Flake8, Pylint)

## Known Limitations

1. Resource limits (memory/CPU) are enforced via:
   - Timeout (3 seconds wall clock time)
   - Output limiting (prevents memory exhaustion)
   - Docker container limits in production

2. Tests use mocking for:
   - WebSocket connections
   - Database operations
   - File system operations

## Future Improvements

- [ ] Add integration tests with real WebSocket
- [ ] Add stress testing for 100+ concurrent users
- [ ] Add security penetration testing
- [ ] Add frontend JavaScript tests
- [ ] Add database migration tests