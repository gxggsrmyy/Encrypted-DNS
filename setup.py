import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="encrypted-dns",
    version="1.1.4",
    author="Xiaoyang Liu",
    author_email="admin@siujoeng-lau.com",
    description="DNS-over-HTTPS and DNS-over-TLS server and forwarder.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Siujoeng-Lau/Encrypted-DNS",
    packages=setuptools.find_packages(),
    package_data={
        'encrypted_dns': ['filter_lists/*.txt'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Internet :: Name Service (DNS)",
        "Topic :: Security :: Cryptography",
        "Topic :: Utilities",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'encrypted-dns=encrypted_dns.main:start'
        ],
    },
    keywords='dns doh dot tls https',
    license='Apache 2.0',
)
