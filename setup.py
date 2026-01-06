"""Setup script for polymarket-data-collector"""

from setuptools import setup, find_packages

setup(
    name="polymarket-data-collector",
    version="0.1.0",
    packages=find_packages(where="."),
    package_dir={"": "."},
    python_requires=">=3.9",
)
