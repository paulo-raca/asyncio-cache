import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='aiocache',
    version='0.0.1',
    author="Paulo Costa",
    author_email="me@paulo.costa.nom.br",
    description="Caching for asyncio projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/paulo-raca/aiocache",
    packages=setuptools.find_packages(),
    extras_require={
        "sqlite": "aiosqlite",
        "test": "aiounittest",
    },
    classifiers=[
        "Topic :: Software Development :: Libraries",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
    ],
)
