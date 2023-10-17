"""
Repo setup file.
"""

from setuptools import find_packages, setup

setup(
    name="eth-fetcher",
    version="0.1",
    packages=find_packages(),
    description="Fetches data from Ethereum blockchain",
    author="Yichen Luo",
    author_email="ucesy34@ucl.ac.uk",
    license="MIT",
    install_requires=["web3", "smart-open", "retry"],
    extras_require={"dev": ["pylint", "black", "pytest"]},
    entry_points={"console_scripts": ["eth-fetcher=eth_fetcher.cli:run"]},
)
