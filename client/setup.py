from setuptools import setup

setup(
    name='pallur',
    version='0.1',
    py_modules=['pallur'],
    install_requires=[
        'Click',
        'requests',
        'pyyaml',
        'click_spinner'
    ],
    entry_points='''
        [console_scripts]
        pallur=pallur_client:pallur_client
    ''',
)