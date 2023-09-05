from setuptools import setup, find_packages


def read_requirements():
    with open('requirements.txt', 'r') as f:
        requirements = f.readlines()
    return [req.strip() for req in requirements if req.strip() and not req.startswith('#')]


setup(
    name='quokka-web',
    version='0.0.1',
    packages=find_packages(exclude=['test', 'test.*']),
    install_requires=read_requirements(),
    author='steveflyer',
    author_email='steveflyer7@gmail.com',
    description='Quokka is a powerful Python library built on top of Playwright, designed to simplify browser automation and web scraping tasks. With Quokka, you can easily navigate web pages, extract data, and interact with page elements using an intuitive API. Quokka supports asynchronous and parallel execution, making it suitable for a wide range of IO and CPU-bound workloads. Get started with Quokka to streamline your browser automation and web scraping workflows.',
    long_description=open('./README.md').read(),
    long_description_content_type='text/markdown',
)
