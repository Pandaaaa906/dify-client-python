from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dify-client-python",
    version="1.0.3",
    author="haoyuhu",
    author_email="im@huhaoyu.com",
    description="A package for interacting with the Dify Service-API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/haoyuhu/dify-client-python",
    license="MIT",
    packages=find_packages(exclude=("tests", "tests.*")),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx",
        "httpx-sse",
        "pydantic>=2,<3",
        "StrEnum",
    ],
    keywords="dify nlp ai language-processing",
    include_package_data=True,
)
