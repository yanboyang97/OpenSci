"""Second independent synthetic fixture to exercise the same engine contract."""
import math


class Quadratic:
    api_version = 1
    version = '1'

    def prepare(self, parameters):
        if not isinstance(parameters, dict) or set(parameters) != {'x', 'offset'}:
            raise ValueError('Quadratic Calculation requires x and offset')
        if any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1e6 for v in parameters.values()):
            raise ValueError('Use finite synthetic parameters bounded by 1e6')
        return dict(parameters)

    def execute(self, prepared):
        return {'value': prepared['x'] ** 2 + prepared['offset']}

    def validate(self, prepared, result):
        return result == self.execute(prepared)
