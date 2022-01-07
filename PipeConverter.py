from typing import Union, Tuple
import numpy as np
from scipy.integrate import odeint


class PipeConverter:
    def __init__(self, d_h: float = 1, c: float = 1) -> None:
        self.d_h = d_h
        self.c = c

    def update_pressure(self, pressure: float) -> None:
        self.d_h = pressure

    def fill_numerically(self, t: np.ndarray, theta: float) -> Tuple[np.ndarray, np.ndarray]:
        def derivative(x, t, delta_h, c, theta):
            return np.sqrt(delta_h / c / x - np.sin(theta) / c)

        # set to be really small number so we don't get divide by 0 errors
        x: np.ndarray = odeint(derivative, 1e-7, t, args=(self.d_h, self.c, theta))
        return t, x

    def equivalent_length(self, length: Union[int, float], d_z: Union[int, float]) -> float:
        """
        Note: This assumes that the pipe fills in less than three minutes.

        :param length: total pipe length
        :param d_z: the height difference of the pipe. Can be negative (but not greater than the assumed d_h)
        :return:
        """

        # if it's pretty much flat just use flat pipe
        if np.abs(d_z) < 0.01:
            return 0.44 * length

        # numerically fill pipe
        # Note: There is a lot of numerical instability here and we might have to sample a lot of points to get decent
        # results. Also need to test with reasonable numbers
        t = np.linspace(0, 5 * 60, 10000)
        theta = np.arcsin(d_z / length)
        t, x = self.fill_numerically(t, theta)
        x = x.reshape(-1)

        # roughly calculate the time it takes to fill through linear interpolation
        tau = np.interp(length, x, t)

        # calculate equivalent stats
        velocity_eq = length / tau
        # TODO: change this to flat pipes (I think just remove d_z terms)
        length_eq = (self.d_h - d_z) / self.c / (velocity_eq ** 2)

        return length_eq
