import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyAutomationAnywhere-minterciso",
    version="0.0.1",
    author="Mateus Interciso",
    author_email="minterciso@gmail.com",
    description="A Python Package to deploy tasks on Automation Anywhere v10.5",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/minterciso/pyAutomationAnywhere",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
