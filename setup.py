from setuptools import setup, find_packages

setup(
    name='EasyGram',
    version='0.0.2',
    description='Библиотека для удобного и многофункционального(в будущем) использования.',
    author='flexyyy',
    packages=find_packages(),
    install_requires=[
        'aiohttp'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    url='https://github.com/flexyyyapk/EasyGram/'
)