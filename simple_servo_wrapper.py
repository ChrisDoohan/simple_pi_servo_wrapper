import json
import pigpio as gpio

from pin_utils import GPIO_to_BCM, PWM_PINS__BCM
from time import sleep

debug_mode = False


class Servo(object):
    io = gpio.pi()

    def __init__(self, servo_conf_path, pin_num=0, use_GPIB_index=True, debug_mode=False):
        self.debug_mode = debug_mode
        self.pin_num = pin_num
        if use_GPIB_index:
            self.pin_num = GPIO_to_BCM[self.pin_num]
        if self.pin_num not in PWM_PINS__BCM:
            raise Exception('Specified pin number {} (GPIO) -- {} (BCM) is not a PWM output pin'.format(
                pin_num, self.pin_num))

        with open(servo_conf_path) as f:
            json_string = f.read()
            conf = json.loads(json_string)

        self.model = conf['model']
        self.PWM_min_us = conf['PWM_min_us']
        self.PWM_max_us = conf['PWM_max_us']
        self.max_travel_degrees = conf['max_travel_degrees']

        travel_lag_numerator__seconds = conf['travel_lag_numerator__seconds']
        travel_lag_denominator__degrees = conf['travel_lag_denominator__degrees']
        self.angular_travel_time__seconds_per_degree = float(
            travel_lag_numerator__seconds) / travel_lag_denominator__degrees
        self.current_position = None

        print('Initializing servo on pin {}'.format(self.pin_num))
        print('Loaded the followng config: \n{}'.format(conf))
        print('Angular speed: {}s/deg ({}s / 90deg)'.format(self.angular_travel_time__seconds_per_degree,
                                                            90 * self.angular_travel_time__seconds_per_degree))
        print('Moving to start position')
        self.reset_position()

    def __repr__(self):
        info_dict = {
            'Servo Model': self.model,
            'PWM Min Width (us)': self.PWM_min_us,
            'PWM Max Width (us)': self.PWM_max_us,
            'Servo Max Travel (deg)': self.max_travel_degrees,
            'Servo Speed (deg/s)': 1.0 / self.angular_travel_time__seconds_per_degree,
            'Current Position': self.current_position
        }
        nice_string = json.dumps(info_dict, indent=4)
        return nice_string

    def _get_travel_time_to(self, new_position):
        if self.current_position is None:
            return self.max_travel_degrees * self.angular_travel_time__seconds_per_degree
        best_estimate = abs(new_position - self.current_position) * self.angular_travel_time__seconds_per_degree
        conservative_estimate = 1.2 * best_estimate
        return conservative_estimate

    def _degrees_to_duty_cycle_us(self, degrees):
        deg_min = 0
        deg_max = self.max_travel_degrees
        degrees += float(deg_max) / 2

        sig_min = self.PWM_min_us
        sig_max = self.PWM_max_us

        us_per_degree = 1.0 * (sig_max - sig_min) / (deg_max - deg_min)

        sig = us_per_degree * degrees + sig_min
        return sig

    def _format_plus(self, num):
        return '+' if num > 0 else ''

    def move_to_position(self, degrees):
        sig_width = self._degrees_to_duty_cycle_us(degrees)
        if not self.PWM_min_us <= sig_width <= self.PWM_max_us:
            raise Exception(
                'Error: position {} degrees is outside the range of the servo. It corresponds to a duty cycle time width of {}us, while this servo supports between {}us and {}us.'
                .format(degrees, sig_width, self.PWM_min_us, self.PWM_max_us))

        expected_travel_time = self._get_travel_time_to(degrees)
        print('Moving position: {}{}->{}{} (PWM duty cycle at {}us). Travel time expectation: {}s'.format(
            self._format_plus(self.current_position),
            self.current_position,
            self._format_plus(degrees),
            degrees,
            sig_width,
            expected_travel_time))
        if not self.debug_mode:
            # do move
            self.io.set_servo_pulsewidth(self.pin_num, sig_width)
            # wait for move to complete
            sleep(expected_travel_time)

        self.current_position = degrees

    def reset_position(self):
        self.move_to_position(0)
