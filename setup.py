from setuptools import setup, find_packages

dependency_links = ['git+https://github.com/ox-inet-resilience/py-distilledESL#egg=py-distilledESL']

setup(name='resilience',
      version='0.2',
      description='System-wide stress testing',
      url='https://github.com/ox-inet-resilience/resilience',
      keywords='abm stress-testing',
      author='INET Oxford',
      author_email='rhtbot@protonmail.com',
      license='Apache',
      packages=find_packages(),
      dependency_links=dependency_links,
      zip_safe=False)
