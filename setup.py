from setuptools import setup, find_packages
from Cython.Build import cythonize

install_requires = [
    'py-economicsl@git+https://github.com/ox-inet-resilience/py-economicsl@master',
    'numpy'
]

cys = (
    ['resilience/contracts/%s.py' % i for i in ['TradableAsset', 'AssetCollateral', 'Loan']] +
    ['resilience/markets/%s.py' %i for i in ['Market', 'AssetMarket']]
)


setup(name='resilience',
      version='0.2',
      description='System-wide stress testing',
      url='https://github.com/ox-inet-resilience/resilience',
      keywords='abm stress-testing',
      author='INET Oxford',
      author_email='rhtbot@protonmail.com',
      license='Apache',
      packages=find_packages(),
      ext_modules=cythonize(cys),
      install_requires=install_requires,
      zip_safe=False)
