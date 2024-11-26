from setuptools import setup, find_packages

setup(
    name="code_extractor",
    version="0.1.0",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        'pytest>=7.0.0',
        'astroid>=3.0.0',  # For Python code parsing
    ],
    extras_require={
        'dev': [
            'pytest-cov>=4.0.0',  # For test coverage reporting
            'black>=23.0.0',      # For code formatting
            'pylint>=3.0.0',      # For code linting
        ]
    }
)
