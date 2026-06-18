from setuptools import setup

package_name = 'marv_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=['marv_control', 'marv_control.lib', 'marv_control.missions'],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pyyaml'],
    zip_safe=True,
    maintainer='eagleauv',
    maintainer_email='dragontomb35782@gmail.com',
    description='Marv AUV master control and mission behaviors',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'master_control_node = marv_control.master_control_node:main',
            'mission_planner_node = marv_control.mission_planner_node:main',
            'auv_keyboard_teleop_node = marv_control.auv_keyboard_teleop_node:main',
            'demo_recorder_node = marv_control.demo_recorder_node:main',
            'demo_replay_node = marv_control.demo_replay_node:main',
        ],
    },
)
