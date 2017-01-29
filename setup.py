from setuptools import setup

setup(
    name='readinglist',
    version='0.1',
    packages=['readinglist'],
    license='MIT',
    entry_points='''
        [console_scripts]
        rl=readinglist.main:main
    ''',
)
