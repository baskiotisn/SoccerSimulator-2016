from setuptools import setup, find_packages

import soccersimulator

setup(
    name='soccer-simulator',
    version='1.0.2016',
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
