import sys

from setuptools import setup
from pyhydroquebec.__version__ import VERSION

if sys.version_info < (3,8):
    sys.exit('Sorry, Python < 3.8 is not supported')

requirements = open('requirements.txt')
install_requires = list(val.strip() for val in requirements)
requirements.close()

test_requirements = open('test_requirements.txt')
tests_require = list(val.strip() for val in test_requirements)
test_requirements.close()

setup(name='pyhydroquebec',
      version=VERSION,
      description='Get your Hydro Quebec consumption (wwww.hydroquebec.com)',
      author='Hervé Lauwerier',
      author_email='hervelauwerier@gmail.com',
      url='http://github.com/heehoo59/pyhydroquebec',
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
        'Programming Language :: Python :: 3.9'
      ]

      )
