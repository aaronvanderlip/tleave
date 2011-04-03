import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'SQLAlchemy==0.5.1',
    'transaction',
    'repoze.tm2',
    'zope.sqlalchemy',
    'FeedParser',
    'beaker',
    'BeautifulSoup',
    'pyramid_zcml'
    'Chameleon<1.9999'
    ]

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='tleave',
      version='0.1',
      description='tleave',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: BFG",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='tleave',
      install_requires = requires,
      entry_points = """\
      [paste.app_factory]
      app = tleave.run:app
      """
      )

