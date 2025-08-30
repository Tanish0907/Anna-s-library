from setuptools import setup, find_packages

# Read the requirements from the 'req.txt' file
def parse_requirements(filename):
    with open(filename, 'r') as f:
        return f.read().splitlines()

# List dependencies from requirements file
requirements = parse_requirements('req.txt')

setup(
    name="Anna'sLibrary",  # Package name
    version="1.0",
    description="A simple Python application for web scraping books",
    long_description="This application includes a web scraper and a UI for managing book searches.",
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="sharmatanish097654@gmail.com",
    url="https://github.com/Tanish0907/Anna-s-library",  # URL for your project (e.g., GitHub)
    packages=find_packages(),  # Automatically find and include packages in the project
    install_requires=requirements,  # External dependencies from req.txt
    entry_points={
        'console_scripts': [
            'scraper=API.AnnasLibrary.Scraper:main',  # Main entry for the scraper script
            'ui=UI.main:main',  # Main entry for the UI script
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',  # Minimum Python version
)
