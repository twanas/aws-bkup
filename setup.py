from distutils.core import setup

setup(
    name='aws-bkup',
    version='0.1',
    py_modules=['aws_bkup',],
    license='MIT',
    author='antoine waugh',
    author_email='antoine@reltech.com',
    url='http://github.com/twanas/aws-bkup',
    description='utility to backup server-side logs to aws s3.',
    long_description=open('README').read(),
    install_requires=['configparser','awscli']
)
