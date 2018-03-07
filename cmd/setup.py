from setuptools import setup

setup(
  name='Pallur',
  version='0.0.1',
  py_modules=['pallur'],
  install_requirements=[
    'Click',
    'python_ldap',
    'docker'
  ],
  entry_points='''
    [console_scripts]
    pallur=pallur:pallur
  ''',
)
