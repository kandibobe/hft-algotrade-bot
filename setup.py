from setuptools import setup, find_packages

setup(
    name="stoic_citadel",
    version="1.0.0",
    packages=find_packages(include=['src*']),
    author="Stoic Citadel Team",
    description="A hybrid Mid-Frequency Trading (MFT) system.",
    install_requires=[
        # Dependencies will be managed via requirements.txt
    ],
    python_requires='>=3.10',
)
