"""Package setup"""
import setuptools


with open("README.md", "r") as f:
    long_description = f.read()

requirements = [
    "click==8.1.3",
    "requests==2.28.1",
    "rich==13.0.0",
    "Mastodon.py==1.8.0",
    "dropbox==11.36.0",
    "beautifulsoup4==4.11.1",
    "openai==0.27.2",
    "pillow==9.4.0",
    "plexapi==4.13.2",
    "cryptography==3.3.2",
    "tiktoken==0.3.2"
]


setuptools.setup(
    name="mastodon-bot-cli",
    version="0.7.7",
    author="Robert Evans",
    description="various commands to interact with a mastodon instance",
    packages=setuptools.find_packages(exclude=["dist", "build", "*.egg-info", "tests"]),
    long_description=long_description,
    long_description_content_type="text/markdown",
    zip_safe=True,
    install_requires=requirements,
    entry_points={"console_scripts": ["mastodonbotcli = src.app:cli"]},
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Development Status :: 1 - Alpha",
    ],
)
