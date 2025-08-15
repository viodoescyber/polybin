from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="polybin",
    version="0.1.0",
    author="viodoescyber",
    description="Smash formats together. Break assumptions. Build valid chaos. A polyglot builder for ICO, MP4, and ZIP files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/viodoescyber/polybin",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "Pillow>=11.2.1"
    ],
    entry_points={
        "console_scripts": [
            "polybin=polybin.cli:main"
        ]
    },
    python_requires='>=3.9',
)