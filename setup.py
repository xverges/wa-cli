from setuptools import find_packages, setup

# From https://stackoverflow.com/a/50368460/239408
# See other answers about why it is not a great practice to use the
# detailed requirements.txt as the source for this
with open('requirements.txt', 'r') as f:
    install_requires = [
        s for s in [
            line.strip(' \n') for line in f
        ] if not s.startswith('#') and s != ''
    ]


setup(
    name='wa_cli',
    version='0.1',
    # py_modules=['wa_cli'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    entry_points='''
        [console_scripts]
        wa-cli=wa_cli:entry_point
    ''',
)
