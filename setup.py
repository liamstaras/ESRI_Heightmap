import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="esri_heightmap-liamstaras",
    version="1.0.0",
    author="Liam Staras",
    author_email="liam.staras@gmail.com",
    description="a script to convert ESRI Grid ASCII to heightmaps",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/liamstaras/ESRI_Heightmap",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)