from setuptools import setup

setup(name='standoffconverter',
      version='0.3',
      description='converter from and to standoff',
      url='https://github.com/millawell/standoffconverter',
      author='David Lassner',
      author_email='lassner@tu-berlin.de',
      license='MIT',
      packages=['standoffconverter'],
      install_requires=[
          'lxml',
          'numpy'
      ],
      zip_safe=False)
