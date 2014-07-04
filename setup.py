from setuptools import setup, find_packages

setup(
    name="pyxshcl",
    version="0.0dev",
    description="Python libraries/tools for XS HCL work.",
    author="Sagnik Datta, Rob Dobson",
    author_email=', '.join([
        "sagnik.datta@citrix.com",
        "rob.dobson@citrix.com",
    ]),
    url="http://unspeicifed.yet",
    packages=find_packages(),
    install_requires=['jira-python'],
    tests_require=[
        "nose",
    ],
    test_suite="nose.collector",
    entry_points={
        'console_scripts': [
            'acklogparser = xscertparser.cmd.acklogparser:main',
            'processsubmission = xsautowf.cmd.processsubmission:main',
            'hclanalysis = xsautowf.cmd.hclanalysis:main',
        ],
    },
)
