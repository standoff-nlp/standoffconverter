from setuptools import setup

setup(name='standoffconverter',
      version='0.8.10',
      description='converter from xml to standoff and back',
      url='https://github.com/standoff-nlp/standoffconverter',
      author='David Lassner',
      author_email='lassner@tu-berlin.de',
      license='MIT',
      packages=['standoffconverter'],
      install_requires=[
          'lxml',
          'numpy',
          'pandas',
          'tqdm'
      ],
      zip_safe=False)
