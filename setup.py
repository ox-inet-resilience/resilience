from setuptools import setup, find_packages, Extension

install_requires = [
    'economicsl@git+https://github.com/ox-inet-resilience/py-economicsl@master',
    'numpy'
]

extmods = [
    # Repo annotation is disabled for now
    Extension("resilience.contracts.%s" % i, sources=['resilience/contracts/%s.py' % i]) for i in ['TradableAsset', 'AssetCollateral', 'Loan', 'Deposit']] + [
        Extension("resilience.markets.%s" % i, sources=['resilience/markets/%s.py' % i]) for i in ['Market', 'AssetMarket']]


setup(name='resilience',
      version='0.4',
      description='System-wide stress testing',
      url='https://github.com/ox-inet-resilience/resilience',
      keywords='abm stress-testing',
      author='INET Oxford',
      author_email='rhtbot@protonmail.com',
      license='Apache',
      packages=find_packages(),
      ext_modules=extmods,
      setup_requires=['setuptools>=18.0', 'cython'],
      install_requires=install_requires,
      zip_safe=False)
