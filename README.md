# Blackbench

[![CI](https://github.com/ichard26/blackbench/actions/workflows/ci.yaml/badge.svg)](https://github.com/ichard26/blackbench/actions/workflows/ci.yaml)
[![Documentation Status](https://readthedocs.org/projects/blackbench/badge/?version=latest)](https://blackbench.readthedocs.io/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/blackbench)](https://pypi.org/project/blackbench/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/blackbench.svg)](https://pypi.org/project/blackbench/)
[![Codecov](https://codecov.io/gh/ichard26/blackbench/branch/main/graph/badge.svg?token=PNX8G0CDUS)](https://codecov.io/gh/ichard26/blackbench)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A benchmarking suite for Black, the Python code formatter. It’s intended to help
quantify changes in performance between versions of Black in a robust and repeatable
manner. Especially useful for verifying a patch doesn’t introduce performance
regressions.

Helpful links:

- [User documentation](https://blackbench.readthedocs.io/en/stable/index.html)
- [Contributing documentation](https://blackbench.readthedocs.io/en/latest/contributing.html)
- [Changelog](https://blackbench.readthedocs.io/en/latest/changelog.html)
- [Chat on Discord](https://discord.gg/RtVdv86PrH)

## License

Blackbench: MIT.

Targets based off real code maintain their original license. Please check the directory
containing the target in question for a license file. There's also one task based off
Black's code. Please also check the task templates directory for more information.
