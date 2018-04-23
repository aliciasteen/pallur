from setuptools import setup

setup(
    name='pallur',
    version='1',
    py_modules=['pallur'],
    install_requirements=[
        'Click',
        'requests',
        'pyyaml',
        'click_spinner'
    ],
    entry_points='''
        [console_scripts]
        pallur=pallur:pallur
    ''',
)
