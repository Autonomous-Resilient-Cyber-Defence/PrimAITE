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
    version="1.0.0",
    install_requires=[
        "gym==0.21.0",
        "matplotlib == 3.5.2",
        "networkx == 2.6.3",
        "numpy == 1.21.1",
        "stable_baselines3 == 1.6.0",
        "pandas == 1.1.5",
        "pyyaml == 6.0",
        "typing-extensions == 4.2.0",
        "torch == 1.12.0"
    ],
    packages=find_packages()
)
