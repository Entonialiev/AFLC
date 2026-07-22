from setuptools import setup, find_packages

setup(
    name="aflc",
    version="2.0.0-alpha1",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
    ],
    python_requires=">=3.9",
    author="Elshan Aliev",
    description="Adaptive Feedback Loop Core — industrial-grade framework for AI agent self-correction",
    license="MIT",
)
