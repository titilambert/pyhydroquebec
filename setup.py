import sys

from setuptools import setup
from pyhydroquebec.__version__ import VERSION

if sys.version_info < (3,4):
    sys.exit('Sorry, Python < 3.4 is not supported')

install_requires = list(val.strip() for val in open('requirements.txt'))
tests_require = list(val.strip() for val in open('test_requirements.txt'))

setup(name='pyhydroquebec',
      version=VERSION,
      description='Get your Hydro Quebec consumption (wwww.hydroquebec.com)',
      author='Thibault Cohen',
      author_email='titilambert@gmail.com',
      url='http://github.com/titilambert/pyhydroquebec',
      package_data={'': ['LICENSE.txt']},
      include_package_data=True,
      packages=['pyhydroquebec'],
      entry_points={
          'console_scripts': [
              'pyhydroquebec = pyhydroquebec.__main__:main',
              'mqtt_pyhydroquebec = pyhydroquebec.__main__:mqtt_daemon'
          ]
      },
      license='Apache 2.0',
      install_requires=install_requires,
      tests_require=tests_require,
      classifiers=[
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
      ]

)
