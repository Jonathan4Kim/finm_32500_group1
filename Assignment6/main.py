import unittest
import os
import sys
import coverage


def main():
    """
    Run all unit tests for the backtester project using unittest + coverage.
    Enforces a minimum coverage threshold of 85%.
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    cov = coverage.Coverage(source=["Assignment6"], omit=["*/Tests/*", "main.py"])
    cov.start()

    print("Running unit tests with coverage...\n")

    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="Tests")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    cov.stop()
    cov.save()

    print("\nCoverage Report:\n")
    cov.report(show_missing=True)

    coverage_percent = cov.report(show_missing=False)
    threshold = 80.0

    if not result.wasSuccessful():
        print("\nSome tests failed.")
        sys.exit(1)
    elif coverage_percent < threshold:
        print(f"\nCoverage below threshold: {coverage_percent:.1f}% (minimum {threshold}%)")
        sys.exit(1)
    else:
        print(f"\nAll tests passed! Coverage: {coverage_percent:.1f}%")
        sys.exit(0)


if __name__ == "__main__":
    main()