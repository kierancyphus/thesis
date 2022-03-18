from typing import Union, Tuple
import numpy as np
from scipy.integrate import odeint
from SimulationTimeGuesser import SimulationTimeGuesser
from FrictionFactorCalculator import FrictionFactorCalculator


class PipeConverter:
    def __init__(self, d_h: float = 1, c: float = 1, f: float = 0.04) -> None:
        self.d_h = d_h
        # TODO: make this a local variable
        # self.f has to be updated on a per pipe basis, and done before self.c
        self.f = f
        # self.c has to be updated on a per pipe basis
        self.c = c
        self.g = 9.81
        self.roughness = 100

    def update_pressure(self, pressure: float) -> None:
        self.d_h = pressure

    def _calculate_f(self, length: Union[int, float], diameter: float):
        friction_calculator = FrictionFactorCalculator(length, diameter, self.d_h, self.roughness)
        self.f = friction_calculator.get_friction_factor()

    def _calculate_c(self, diameter: Union[float, int]) -> None:
        # Calculates the internal value of C according to the Darcy-Weisback Equation
        # The pipe friction factors are chosen based on calibration data
        self.c = self.f / diameter / 2 / self.g

    def _fill_numerically(self, t: np.ndarray, theta: float, flat: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        def derivative(x, t, delta_h, c, theta):
            return np.sqrt(delta_h / c / x - np.sin(theta) / c)

        def derivative_flat(x, t, delta_h, c):
            return np.sqrt(delta_h / c / x)

        def derivative_laminar_flow(x, t, delta_h, theta, d, g):
            return ((d ** 2) * g / 32 / x) * (delta_h - x * np.sin(theta))

        # x: np.ndarray = odeint(derivative_laminar_flow, 1e-7, t, args=(self.d_h, theta, 0.3, self.g))
        # set to be really small number so we don't get divide by 0 errors
        if flat:
            x: np.ndarray = odeint(derivative_flat, 1e-7, t, args=(self.d_h, self.c))
        else:
            x: np.ndarray = odeint(derivative, 1e-7, t, args=(self.d_h, self.c, theta))
        return t, x

    def fill_time(self, length: Union[int, float], d_z: Union[int, float], diameter: Union[int, float],
                  update_f: bool = True, update_pressure: bool = True, return_fronts: bool = False) -> float:
        # if it's pretty much flat just use flat pipe
        is_flat = np.abs(d_z) < 0.01

        # update the friction factor and assumed pressure
        if update_f:
            self._calculate_f(length, diameter)
        self._calculate_c(diameter)

        if (not is_flat) and update_pressure:
            # TODO: Should change this so it is max(2 * d_z, base_pressure) otherwise pipes that are slightly only
            #  slightly slanted will have really strange fill times
            self.update_pressure(2 * np.abs(d_z))

        # estimate simulation time needed
        max_simulation_time = SimulationTimeGuesser(length, d_z, self.c, 100, type="poly_length_offset").evaluate()

        # numerically fill pipe
        # t = np.arange(start=0, stop=max_simulation_time, step=3)
        t = np.linspace(0, max_simulation_time, 10000)
        theta = np.arcsin(d_z / length)
        t, x = self._fill_numerically(t, theta, is_flat)
        x = x.reshape(-1)

        # roughly calculate the time it takes to fill through linear interpolation
        tau = np.interp(length, x, t)

        return (tau, t, x) if return_fronts else tau

    def equivalent_length(self, length: Union[int, float], d_z: Union[int, float], diameter: Union[int, float],
                          update_pressure: bool = True) -> float:
        """
        Note: This assumes that the pipe fills in less than three minutes.

        :param diameter: diameter of pipe used in calculating friction coefficient
        :param length: total pipe length
        :param d_z: the height difference of the pipe. Can be negative (but not greater than the assumed d_h)
        :return:
        """

        # if it's pretty much flat just use flat pipe
        is_flat = np.abs(d_z) < 0.01
        if is_flat:
            return ((2 / 3) ** 2) * length

        tau = self.fill_time(length, d_z, diameter, update_pressure=update_pressure)

        # calculate equivalent stats
        velocity_eq = length / tau
        length_eq = (self.d_h - d_z) / self.c / (velocity_eq ** 2)

        return length_eq
