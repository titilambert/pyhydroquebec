from pip.req import parse_requirements
from setuptools import setup
from pip.download import PipSession

session = PipSession()
install_reqs = parse_requirements('requirements.txt', session=session)
test_reqs = parse_requirements('test_requirements.txt', session=session)

setup(name='pyhydroquebec',
      version='1.2.0',
      description='Get your Hydro Quebec consumption (wwww.hydroquebec.com)',
      author='Thibault Cohen',
      author_email='titilambert@gmail.com',
      url='http://github.org/titilambert/pyhydroquebec',
      packages=['pyhydroquebec'],
      entry_points={
          'console_scripts': [
              'pyhydroquebec = pyhydroquebec.__main__:main'
          ]
      },
      install_requires=[str(r.req) for r in install_reqs],
      tests_require=[str(r.req) for r in test_reqs],
)
