from setuptools import setup
from rak_net import __version__


requirements = [
    'binary-utils',
]

extras_require = {
    'docs': [
        'sphinx',
        'sphinx-rtd-theme',
    ],
}

packages = [
    'rak_net',
]

with open('README.rst') as f:
    readme = f.read()


setup(
    name='aio-rak-net',
    author='L0RD-ZER0',
    url='',
    version=__version__,
    license='MIT',
    description='Async Rak-Net',
    long_description=readme,
    long_description_content_type="text/x-rst",
    install_requires=requirements,
    extras_require=extras_require,
    packages=packages,
)
