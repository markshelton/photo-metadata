try:
    from setuptools import setup
except ImportError:
    print("WARNING: setuptools not installed. Will try using distutils instead..")
    from distutils.core import setup

setup(name='thickshake',
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
      packages=['thickshake'],
      test_suite='tests',
      zip_safe=False)