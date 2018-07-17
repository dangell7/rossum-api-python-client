from setuptools import setup

setup(name='rossum',
      version='0.1.1',
      description='Rossum Elis Extraction API client for AI-based invoice extraction',
      url='https://github.com/rossumai/rossum-api-python-client',
      author='Bohumir Zamecnik, Rossum, Ltd.',
      author_email='bohumir.zamecnik@rossum.ai',
      license='MIT',
      packages=['rossum'],
      zip_safe=False,
      install_requires=[
        'requests',
        'polling',
      ],
      setup_requires=['setuptools-markdown'],
      long_description_markdown_filename='README.md',
      # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          # How mature is this project? Common values are
          #   3 - Alpha
          #   4 - Beta
          #   5 - Production/Stable
          'Development Status :: 3 - Alpha',

          'Intended Audience :: Developers',
          'Topic :: Office/Business :: Financial :: Accounting',
          'Topic :: Scientific/Engineering :: Image Recognition',
          'Topic :: Text Processing :: General',

          'License :: OSI Approved :: MIT License',

          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',

          'Operating System :: POSIX :: Linux',
      ],
      entry_points={
          'console_scripts': [
              'rossum = rossum.__main__:main',
          ]
      },)
