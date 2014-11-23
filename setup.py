from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='mydinosaur',
    version='0.1.dev0',
    description='A simple RSS feed generator for bot-makers',
    long_description="",
    url='https://github.com/aparrish/mydinosaur',
    author='Allison Parrish',
    author_email='allison@decontextualize.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='rss twitter bots',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=[
			'Jinja2>=2.7.3',
			'PyRSS2Gen>=1.1',
			'boto>=2.34.0',
			'feedparser>=5.1.3',
			'python-dateutil>=2.2'
		],
    extras_require = {},
    package_data={},
    data_files=[],
    entry_points={},
)
