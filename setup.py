# vim:et:ts=4:sts=4:ai

from setuptools import setup, find_packages
setup(
    name = "pysk",
    version = "0.0.2",
    packages = find_packages(),
    install_requires = [
        "signalk_client>=0.2,<0.3",
        ],
    entry_points={
        'console_scripts': [
            'pysk = pysk.pysk:main',
        ],
    },
    author = "Philip J Freeman",
    author_email = "elektron@halo.nu",
    description = "client application to display streaming data from a signalk server via curses and other user interfaces",
    license = "GPL3",
    keywords = "signalk curses",
    url = "https://github.com/ph1l/pysk",
)
