from distutils.core import setup
from setuptools import find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
import sys
import re

if sys.version_info[0] == 2:
    sys.exit("Sorry, Python 2 is not supported.")


def obtain_version():
    """
    Obtains the version as specified in prophesy.
    :return: Version of prophesy.
    """
    verstr = "unknown"
    try:
        verstrline = open('paynt/_version.py', "rt").read()
    except EnvironmentError:
        pass  # Okay, there is no version file.
    else:
        VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
        mo = re.search(VSRE, verstrline, re.M)
        if mo:
            verstr = mo.group(1)
        else:
            raise RuntimeError("unable to find version in paynt/_version.py")
    return verstr


class ConfigDevelop(develop):
    """
    Custom command to write the config files after installation
    """
    user_options = develop.user_options

    def initialize_options(self):
        develop.initialize_options(self)

    def finalize_options(self):
        develop.finalize_options(self)

    def run(self):
        develop.run(self)


class ConfigInstall(install):
    """
    Custom command to write the config files after installation
    """

    user_options = install.user_options

    def initialize_options(self):
        install.initialize_options(self)

    def finalize_options(self):
        install.finalize_options(self)

    def run(self):
        install.run(self)


setup(
    name="paynt",
    version=obtain_version(),
    author="Sebastian Junges",
    author_email="sebastian.junges@cs.rwth-aachen.de",
    maintainer="Sebastian Junges",
    maintainer_email="sebastian.junges@cs.rwth-aachen.de",
    license="GPLv3",
    url="https://github.com/randriu/synthesis",
    description="PAYNT (Probabilistic progrAm sYNThesizer)",
    long_description=
    "PAYNT (Probabilistic progrAm sYNThesizer) is a tool for automated synthesis of probabilistic programs.",
    packages=find_packages(),
    install_requires=['click', 'stormpy', 'z3-solver'],
    extras_require={},
    package_data={
        'paynt': [],
    },
    scripts=[
        'paynt.py'
    ],
    cmdclass={
        'develop': ConfigDevelop,
        'install': ConfigInstall,
    }
)
