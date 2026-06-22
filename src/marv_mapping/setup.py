from setuptools import find_packages, setup

package_name = 'marv_mapping'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'numpy'],
    zip_safe=True,
    maintainer='eagleauv',
    maintainer_email='dragontomb35782@gmail.com',
    description='Marv AUV mapping node (landmarks + dead reckoning)',
    license='MIT',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'mapping_node = marv_mapping.mapping_node:main',
        ],
    },
)
