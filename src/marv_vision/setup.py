from setuptools import setup

package_name = 'marv_vision'

setup(
    name=package_name,
    version='0.0.0',
    packages=['marv_vision', 'marv_vision.lib', 'marv_vision.weights'],
    package_data={'marv_vision.weights': ['*.pt']},
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='eagleauv',
    maintainer_email='dragontomb35782@gmail.com',
    description='Marv AUV vision processing (front and down cameras)',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'f_cam_node = marv_vision.f_cam_node:main',
            'd_cam_node = marv_vision.d_cam_node:main',
        ],
    },
)
