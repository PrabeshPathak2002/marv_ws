from setuptools import setup

package_name = 'marv_ardusub'

setup(
    name=package_name,
    version='0.0.0',
    packages=['marv_ardusub', 'marv_ardusub.lib'],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='eagleauv',
    maintainer_email='dragontomb35782@gmail.com',
    description='Marv AUV ArduSub hardware interface',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'ardusub_node = marv_ardusub.ardusub_node:main',
            'unity_hil_bridge = marv_ardusub.unity_hil_bridge:main',
        ],
    },
)
