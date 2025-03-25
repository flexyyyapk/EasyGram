from setuptools import setup, find_packages

setup(
    name='EasyGram',
    version='0.0.4.2',
    description='Библиотека для удобного и многофункционального(в будущем) использования.',
    long_description=open('C:/Users/CHRON/PycharmProjects/pythonProject/Tests/TestEasyGram/readme.md', encoding='utf-8').read()+'\n\n'+open('C:/Users/CHRON/PycharmProjects/pythonProject/Tests/TestEasyGram/EasyGram/whatsnew.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='flexyyy',
    packages=find_packages(),
    package_data={
        "": ['readme.md']
    },
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