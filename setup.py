#!/usr/bin/env python
"""Setup script for notion-performance-summaries package."""

from setuptools import setup, find_packages


def read_readme():
    """Read README.md file."""
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Generate performance summaries for chipmunk lab data and upload them to Notion."


setup(
    name="notion-performance-summaries",
    version="0.1.0",
    description="Generate performance summaries for chipmunk using matlab and labdata-tools and upload them to Notion",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Gabriel Rojas",
    url="https://github.com/rojasgabriel/notion_performance_summaries",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "notion_summaries=notion_summaries:cli",
        ],
    },
)
