import setuptools
import dScriptModule

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='dScriptModule',
    version=dScriptModule.__version__,
    url='https://github.com/mk-maddin/dScriptModule',
    author='Martin Kraemer',
    author_email='mk.maddin@gmail.com',
    description='Home Assistant ready python module for dScript boards (by Robot-Electronics / Devantech Ltd.) with CUSTOM app firmware',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=[
        'bitstring',],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
