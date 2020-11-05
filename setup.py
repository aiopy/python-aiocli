from setuptools import setup, find_packages
from pytoml import load

with open('pyproject.toml', 'rb') as file:
    metadata = load(file)['metadata']

with open('README.md', 'r') as file:
    long_description = file.read()

author = metadata['authors'][0].split(' ')[0]

setup(
    name=metadata['name'],
    version=metadata['version'],
    description=metadata['description'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    license=metadata['license'],
    author=author,
    author_email=metadata['authors'][0].split(' ')[1],
    url=metadata['repository'],
    documentation=metadata['documentation'],
    classifiers=metadata['classifiers'],
    keywords=metadata['keywords'],
    python_requires='>=3.6',
    packages=find_packages(),
)
