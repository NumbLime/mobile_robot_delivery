from glob import glob
from os.path import join

from setuptools import find_packages, setup

package_name = 'delivery_task_manager'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='numblime',
    maintainer_email='Numblime@gmail.com',
    description='Sequential pickup and drop-off navigation task server.',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'delivery_task_server = '
            'delivery_task_manager.delivery_task_server:main',
            'delivery_acceptance_client = '
            'delivery_task_manager.acceptance_client:main',
        ],
    },
)
