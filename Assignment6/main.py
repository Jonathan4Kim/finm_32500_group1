import pytest
import sys
import os

def main():
    """
    Run all unit tests for the backtester project using pytest.
    Includes coverage reporting and enforces a minimum coverage threshold.
    """

    # Make sure we're running from the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    # Define pytest arguments
    pytest_args = [
        "-q",                     # quiet mode (concise output)
        "--color=yes",            # colored output
        "--disable-warnings",     # ignore warnings for cleaner output
        "--maxfail=1",            # stop after first failure (optional)
        "--cov=backtester",       # measure coverage for the backtester package
        "--cov-report=term-missing",  # show lines missing coverage
        "--cov-fail-under=90",    # require at least 90% coverage
        "tests",                  # folder containing test files
    ]

    print("🔍 Running unit tests with coverage...\n")
    exit_code = pytest.main(pytest_args)

    # Exit with pytest's return code (important for CI)
    if exit_code == 0:
        print("\nAll tests passed and coverage threshold met!")
    else:
        print("\nSome tests failed or coverage below threshold.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
