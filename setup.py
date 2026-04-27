"""
TaniWise Bot Setup Configuration
"""
from setuptools import setup, find_packages

setup(
    name="taniwise-bot",
    version="1.0.0",
    description="WhatsApp AI Assistant for Indonesian Farmers",
    author="TaniWise Team",
    author_email="team@taniwise.id",
    url="https://github.com/pranatamangsa/taniwise-bot",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "azure-functions==1.17.0",
        "azure-cosmos==4.5.1",
        "azure-identity==1.14.0",
        "requests==2.31.0",
        "python-dotenv==1.0.0",
        "openai==1.3.0",
        "Pillow==10.0.1",
        "aiohttp==3.9.0"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Farmers",
        "Topic :: Agriculture",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
