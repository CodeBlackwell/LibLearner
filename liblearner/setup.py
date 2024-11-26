from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="liblearner",
    version="0.1.0",
    author="LibLearner Team",
    description="A library for extracting and analyzing code from various file types",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/codeblackwell/liblearner",
    packages=find_packages(include=['liblearner', 'liblearner.*']),
    scripts=[
        'bin/process_files',
        'bin/scout_extensions'
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
    install_requires=[
        "astunparse>=1.6.3",
        "python-magic>=0.4.27",
        "pandas",
        "typing",
        "pathlib",
        "nbformat>=5.0.0",  # For Jupyter notebook processing
    ],
)
