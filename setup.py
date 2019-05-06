from setuptools import setup, find_packages

install_requires = ['py-economicsl@git+https://github.com/ox-inet-resilience/py-economicsl@master']

setup(name='resilience',
      version='0.2',
      description='System-wide stress testing',
      url='https://github.com/ox-inet-resilience/resilience',
      keywords='abm stress-testing',
      author='INET Oxford',
      author_email='rhtbot@protonmail.com',
      license='Apache',
      packages=find_packages(),
      install_requires=install_requires,
      zip_safe=False)
