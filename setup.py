from setuptools import setup, find_packages
import os

PACKAGE_NAME = "soccersimulator"


def read_package_variable(key):
    """Read the value of a variable from the package without importing."""
    module_path = os.path.join(PACKAGE_NAME, '__init__.py')
    with open(module_path) as module:
        for line in module:
            parts = line.strip().split(' ')
            if parts and parts[0] == key:
                return parts[-1].strip("'")
    assert 0, "'{0}' not found in '{1}'".format(key, module_path)



setup(
    name=read_package_variable('__project__'),
    version=read_package_variable('__version__'),
    url='https://github.com/baskiotisn/soccersimulator/',
    license='GPL',
    author='Nicolas Baskiotis',
    install_requires=['numpy',
                    'pyglet',
                    ],
    author_email='nicolas.baskiotis@lip6.fr',
    description='Soccer Simulator and MDP for 2I013 UPMC project',
    packages=find_packages()
)
