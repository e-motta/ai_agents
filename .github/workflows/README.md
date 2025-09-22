# GitHub Actions CI/CD Workflows

This directory contains GitHub Actions workflows for automated testing and quality checks.

## Workflows

### 1. `ci.yml` - Comprehensive CI Pipeline

A full CI pipeline that runs on pull requests and pushes to main/develop branches.

**Features:**

- **Multi-Python Testing**: Tests on Python 3.9, 3.11, and 3.12
- **Test Coverage**: Runs all tests with coverage reporting
- **Code Quality**: Linting with flake8, black, isort, and mypy
- **Security**: Security checks with safety and bandit
- **Coverage Upload**: Uploads coverage reports to Codecov

**Jobs:**

- `test`: Runs unit tests, API tests, and coverage analysis
- `lint`: Code quality and formatting checks
- `security`: Security vulnerability scanning

### 2. `tests.yml` - Simple Test Runner

A minimal workflow focused only on running tests.

**Features:**

- **Python 3.11**: Single Python version testing
- **Test Execution**: Runs all tests using the custom test runner
- **Coverage**: Generates coverage reports with 80% threshold

## Usage

### Triggering Workflows

Workflows automatically run on:

- **Pull Requests** to `main` or `develop` branches
- **Pushes** to `main` or `develop` branches

### Manual Execution

You can also trigger workflows manually:

1. Go to the "Actions" tab in your GitHub repository
2. Select the workflow you want to run
3. Click "Run workflow"
4. Choose the branch and click "Run workflow"

### Test Runner Commands

The workflows use the custom `backend/run_tests.py` script with these options:

```bash
# Run all tests
python run_tests.py --type all --verbose

# Run specific test suites
python run_tests.py --type unit      # Unit tests only
python run_tests.py --type chat      # API tests only
python run_tests.py --type router    # Router agent tests
python run_tests.py --type math      # Math agent tests

# Run with coverage
python run_tests.py --type coverage --coverage-fail-under 80

# Generate HTML coverage report
python run_tests.py --type coverage-html
```

## Configuration

### Environment Variables

You may need to set these environment variables in your repository settings:

- `OPENAI_API_KEY`: Required for LLM-based tests
- `REDIS_URL`: Required for Redis-dependent tests

### Coverage Threshold

The default coverage threshold is set to 80%. You can modify this in the workflow files:

```yaml
python run_tests.py --type coverage --coverage-fail-under 80
```

### Python Versions

The comprehensive CI pipeline tests on multiple Python versions:

- Python 3.9
- Python 3.11
- Python 3.12

## Troubleshooting

### Common Issues

1. **Dependency Installation Failures**

   - Check that all dependencies in `requirements.txt` are available
   - Ensure Python version compatibility

2. **Test Failures**

   - Review test output in the Actions logs
   - Check for missing environment variables
   - Verify test data and mocks are working correctly

3. **Coverage Failures**
   - Ensure tests are covering the expected code paths
   - Check for excluded files in coverage configuration

### Viewing Results

- **Test Results**: Check the "Actions" tab for detailed logs
- **Coverage Reports**: Available in the workflow artifacts
- **Security Reports**: Bandit results are logged in the security job

## Customization

### Adding New Test Types

To add new test types, modify `backend/run_tests.py` and update the workflow files accordingly.

### Modifying Quality Checks

You can customize the linting and security checks by modifying the commands in the workflow files.

### Adding New Jobs

To add new jobs (e.g., deployment, integration tests), add them to the workflow files following the existing pattern.
