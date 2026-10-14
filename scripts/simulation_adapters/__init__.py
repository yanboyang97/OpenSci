"""Reviewed registration point. Adding an adapter does not edit the lifecycle engine."""
from simulation_adapters.sum_values import SumValues
from simulation_adapters.quadratic import Quadratic

REGISTRY = {'sum-v1': SumValues(), 'quadratic-v1': Quadratic()}
