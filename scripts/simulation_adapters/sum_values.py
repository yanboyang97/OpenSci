"""Bounded synthetic arithmetic fixture; no external tools or scientific claim."""
import math


class SumValues:
    api_version = 1
    version = '1'

    def prepare(self, parameters):
        if not isinstance(parameters, dict) or set(parameters) != {'values'}:
            raise ValueError('Sum Calculation requires values')
        values = parameters['values']
        if (not isinstance(values, list) or not 1 <= len(values) <= 10000
                or any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1e6 for v in values)):
            raise ValueError('Use 1..10000 finite synthetic values bounded by 1e6')
        return {'values': list(values)}

    def execute(self, prepared):
        return {'sum': math.fsum(prepared['values']), 'count': len(prepared['values'])}

    def validate(self, prepared, result):
        return result == self.execute(prepared)
