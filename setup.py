# vim:et:ts=4:sts=4:ai

from setuptools import setup, find_packages
setup(
    name = "pysk",
    version = "0.0.1",
    packages = find_packages(),
    install_requires = [
        "signalk_client",
        ],
    entry_points={
        'console_scripts': [
            'pysk = pysk.pysk:main',
        ],
    },
    author = "Philip J Freeman",
    author_email = "elektron@halo.nu",
    description = "",
    license = "GPL3",
    keywords = "",
    url = "https://github.com/ph1l/pysk",
)
