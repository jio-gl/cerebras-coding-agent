from setuptools import setup, find_packages

setup(
    name="cerebras-agent",
    version="0.1.0",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "rich>=13.7.0",
        "typer>=0.9.0",
        "gitignore-parser>=0.1.0",
        "cerebras-cloud-sdk>=0.1.0",
        "colorama>=0.4.4",
        "pydantic>=2.0.0",
        "click>=8.0.0",
        "shellingham>=1.5.0",
    ],
    entry_points={
        "console_scripts": [
            "cerebras-agent=cerebras_agent.cli:app",
        ],
    },
    author="Cerebras",
    author_email="info@cerebras.net",
    description="A local agent for code development using Cerebras API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/cerebras/cerebras-coding-agent",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "isort>=5.0.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 