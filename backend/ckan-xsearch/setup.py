import setuptools

with open("README.md", "r") as f:
    long_description = f.read()


setuptools.setup(
    name="xckan",
    version="0.9.1",
    description="Cross-search system for multiple CKAN sites",
    long_description=long_description,
    url="https://github.com/InfoProto/ckan-xsearch",
    packages=['xckan'],
    package_dir={'xckan': '.'},
    classifiers={
        "programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operationg System :: Linux",
    },
    install_requires=[
        'pysolr>=3.9.0', 'requests>=2.24.0',
    ],
    python_requries='>=3.6'
)
