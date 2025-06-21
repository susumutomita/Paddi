from setuptools import setup

with open("requirements.txt", "r") as f:
    required_packages = f.read().splitlines()

setup(
    name="paddi",
    version="0.1",
    packages=[
        "app",
    ],
    install_requires=required_packages,
    entry_points={
        "console_scripts": [
            "paddi=app.main:main",
            "paddi-collector=app.collector.main:main",
            "paddi-explainer=app.explainer.main:main",
            "paddi-reporter=app.reporter.main:main",
        ],
    },
)
