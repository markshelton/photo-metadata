try:
    from setuptools import setup, find_packages
except ImportError:
    print("WARNING: setuptools not installed. Will try using distutils instead..")
    from distutils.core import setup

setup(
    name='thickshake',
    version='1.0.0',
    description='Thickshake helps improve library catalogues',
    url='http://github.com/markshelton/thickshake',
    author='Mark Shelton',
    author_email='mark@shelton.id.au',
    license='None',
    classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Natural Language :: English',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: Implementation :: CPython',
    ],
    packages=find_packages("thickshake"),
    package_dir={"": "thickshake"},
    include_package_data=True,
    entry_points="""
        [console_scripts]
        thickshake=thickshake.cli:cli
    """,
    install_requires=["Click"],
    zip_safe=False
)