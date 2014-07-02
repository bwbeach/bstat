from setuptools import setup, find_packages
import sys, os

version = '0.0.2'

setup(name='bstat',
      version=version,
      description="Data handlig for statistics, with connections to Google Charts",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Brian Beach',
      author_email='bwbeach@beachfamily.net',
      url='http://www.beachfamily.net/bstat/',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
