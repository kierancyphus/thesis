from typing import Union, Tuple
import numpy as np
from scipy.integrate import odeint
from SimulationTimeGuesser import SimulationTimeGuesser


class PipeConverter:
    def __init__(self, d_h: float = 1, c: float = 1) -> None:
        self.d_h = d_h
        self.c = c
        self.g = 9.81

    def update_pressure(self, pressure: float) -> None:
        self.d_h = pressure

    def calculate_c(self, diameter: Union[float, int], f: float = 0.04) -> None:
        # Calculates the internal value of C according to the Darcy-Weisback Equation
        # The pipes are assumed to be smooth and a friction factor of 0.04 is applied
        # TODO: change this to provide different friction factors based on pipes
        self.c = f / diameter / 2 / self.g

    def fill_numerically(self, t: np.ndarray, theta: float) -> Tuple[np.ndarray, np.ndarray]:
        def derivative(x, t, delta_h, c, theta):
            return np.sqrt(delta_h / c / x - np.sin(theta) / c)

        # set to be really small number so we don't get divide by 0 errors
        x: np.ndarray = odeint(derivative, 1e-7, t, args=(self.d_h, self.c, theta))
        return t, x

    def equivalent_length(self, length: Union[int, float], d_z: Union[int, float], diameter: Union[int, float]) -> float:
        """
        Note: This assumes that the pipe fills in less than three minutes.

        :param diameter: diameter of pipe used in calculating friction coefficient
        :param length: total pipe length
        :param d_z: the height difference of the pipe. Can be negative (but not greater than the assumed d_h)
        :return:
        """

        # if it's pretty much flat just use flat pipe
        if np.abs(d_z) < 0.01:
            return 0.44 * length
        # update the friction factor
        self.calculate_c(diameter)
        print(self.c)
        # estimate simulation time needed
        max_simulation_time = SimulationTimeGuesser(length, d_z, 100, type="poly_length_offset").evaluate()
        print(f"max_simulation_time: {max_simulation_time}, * c: {max_simulation_time * self.c}")
        # numerically fill pipe
        t = np.linspace(0, max_simulation_time, 10000)
        theta = np.arcsin(d_z / length)
        t, x = self.fill_numerically(t, theta)
        x = x.reshape(-1)

        # roughly calculate the time it takes to fill through linear interpolation
        tau = np.interp(length, x, t)
        print(f"filling time: {tau}, d_z: {d_z}, length: {length}")

        # calculate equivalent stats
        velocity_eq = length / tau
        # TODO: change this to flat pipes (I think just remove d_z terms)
        length_eq = (self.d_h - d_z) / self.c / (velocity_eq ** 2)

        return length_eq


if __name__ == "__main__":
    converter = PipeConverter()
    converter.update_pressure(10)
    converter.equivalent_length(10000, 10)