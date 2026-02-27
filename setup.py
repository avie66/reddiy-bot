from setuptools import setup, find_packages

setup(
    name="reddiy",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "flexus-client-kit",
        "motor>=3.3.2",
        "pymongo>=4.6.1",
    ],
    package_data={"": ["*.webp", "*.png", "*.html", "*.lark", "*.json"]},
)
