import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid==1.4',
    'SQLAlchemy==0.7.9',
    'transaction==2.1.2',
    'repoze.tm2==2.1',
     'zope.schema==4.4.2',
    'feedparser==5.2.1',
    'Beaker==1.8.1',
    'BeautifulSoup==3.2.1',
    'pyramid-zcml==1.0.0',
    'Chameleon<1.9999'
    ]

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='tleave',
      version='0.3',
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
      package_data={'': ['configure.zcml']},
      include_package_data=True,
      zip_safe=False,
      test_suite='tleave',
      install_requires = requires,
      entry_points = """\
      [paste.app_factory]
      app = tleave.run:app
      """
      )

