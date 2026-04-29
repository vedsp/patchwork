#!/bin/bash

# 1. Clean old builds
rm -rf dist/ build/ *.egg-info

# 2. Build the package (requires 'hatch')
# pip install hatch
hatch build

# 3. Test installation locally
# This ensures the entry points and dependencies are correctly defined
pip install dist/*.whl

# 4. Upload to TestPyPI (Dry run)
# Requires 'twine' (pip install twine)
# Get a token from https://test.pypi.org/
python -m twine upload --repository testpypi dist/*

# 5. Official Publication to PyPI
# python -m twine upload dist/*
