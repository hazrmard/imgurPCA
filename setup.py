from setuptools import setup, find_packages


setup(
    name='imgurpca',
    version='2.3.0',
    description='Machine learning and bots on imgur.com.',
    author='Ibrahim A.',
    author_email='ibrahim78786@gmail.com',
    packages=find_packages(),
    install_requires=['requests', 'numpy', 'imgurpython'],
    url='https://github.com/hazrmard/imgurPCA',
    classifiers=['Development Status :: 3 - Alpha'],
)
