from setuptools import setup

setup(name='simple_pi_servo_wrapper',
      version='0.1',
      description='Convenience wrapper for pigpio',
      url='https://github.com/ChrisDoohan/simple_pi_servo_wrapper',
      author='Chris Doohan',
      author_email='ChrisDoohan@gmail.com',
      install_requires=['pigpio'],
      python_requires='~=3.0',
      license='MIT',
      packages=['simple_pi_servo_wrapper'],
      zip_safe=False)
