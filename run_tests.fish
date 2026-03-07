#!/bin/bash
# run_tests.sh
pytest tests/ -v --log-cli-level=INFO --log-file=tests/test_output.log --cov=. --cov-report=html