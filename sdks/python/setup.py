from setuptools import setup, find_packages

setup(
    name="tokenmeter",
    version="0.1.0",
    description="LLM API cost tracker and smart router — drop-in OpenAI replacement",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="TokenMeter",
    author_email="hello@tokenmeter.dev",
    url="https://github.com/tokenmeter/tokenmeter",
    project_urls={
        "Documentation": "https://docs.tokenmeter.dev",
        "Changelog": "https://github.com/tokenmeter/tokenmeter/blob/main/CHANGELOG.md",
        "Issues": "https://github.com/tokenmeter/tokenmeter/issues",
    },
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0",
            "pytest-cov>=5.0",
            "ruff>=0.4",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="llm openai cost tracking api proxy",
)
