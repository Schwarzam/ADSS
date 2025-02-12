import setuptools

setuptools.setup(
     name='adss',
     version='0.1',
     packages = setuptools.find_packages(),
     author="Gustavo Schwarz",
     author_email="gustavo.b.schwarz@gmail.com",
     description="Astronomical Data Smart System",
     url="https://github.com/schwarzam/adss",
     install_requires = ['requests', 'astropy', 'pyvo'],
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: Apache Software License"
     ],
 )
#python3 setup.py bdist_wheel
#python3 -m twine upload dist/*