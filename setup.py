from setuptools import setup, find_packages
setup(name='PortDebug',
      version='1.0.6',
      description='for using serial port debug',
      url='https://github.com/CraneSun/PortDebug',
      author='Kun Sun',
      author_email='sk602015817@hotmail.com',
      license='MIT',
      packages=find_packages(),
      entry_points={
        'console_scripts': [
            'PortDebug=PortDebug.main:main',  # Ensure this points to the correct function
        ],
      },
      install_requires=['pyside6','py-mini-racer'],  # 依赖包列表
      python_requires='>=3.6',
      zip_safe=False)