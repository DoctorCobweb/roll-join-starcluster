try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'join vector layers with electorate roll',
    'author': 'andre trosky',
    'url': 'https://github.com/DoctorCobweb/roll-join',
    'download_url': 'https://github.com/DoctorCobweb/roll-join',
    'author_email': 'andretrosky@gmail.com',
    'version': '0.0.1',
    'install_requires': ['nose', 'boto'],
    'packages': ['spatial_join'],
    'scripts': [],
    'name': 'spatial_join'
}

setup(**config)
