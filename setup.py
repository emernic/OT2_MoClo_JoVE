from setuptools import setup

setup(name='ot2_moclo_jove',
      version='0.1',
      description='This project allows users to do end-to-end molecular cloning using the OT2 liquid handling robot by OpenTrons.',
      url='https://github.com/emernic/OT2_MoClo_JoVE',
      author='Nick Emery',
      author_email='emernic@bu.edu',
      license='MIT',
      packages=['ot2_moclo_jove'],
      install_requires=[
          'yaml',
          'Pillow'
      ],
      zip_safe=False)