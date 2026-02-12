from setuptools import setup, find_packages

setup(
    name="reddiy",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flexus-client-kit",
        "praw>=7.7.1",
        "prawcore>=2.4.0",
        "motor>=3.3.2",
        "pymongo>=4.6.1",
    ],
    package_data={"": ["*.webp", "*.png", "*.html", "*.lark", "*.json"]},
)
