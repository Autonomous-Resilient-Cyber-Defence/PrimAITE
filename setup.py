# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
Setup
"""

from setuptools import find_packages, setup

setup(
    name="primaite",
    maintainer="QinetiQ Training and Simulation Ltd",
    url="https://github.com/qtsl/PrimAITE",
    description="A primary-level simulation tool",
    python_requires=">=3.7",
    version="1.1.0",
    install_requires=[
        "gym==0.21.0",
        "matplotlib==3.6.2",
        "networkx==2.8.8",
        "numpy==1.23.5",
        "stable_baselines3==1.6.2",
        # Required for older versions of Gym that aren't compliant with
        # Setuptools>=67.
        "setuptools==66"
    ],
    packages=find_packages()
)
