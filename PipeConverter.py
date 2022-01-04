from typing import Union, Tuple
import numpy as np
from scipy.integrate import odeint


class PipeConverter:
    def __init__(self, d_h: float, c: float) -> None:
        self.d_h = d_h
        self.c = c

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
        t = np.linspace(0, 3 * 60, 10000)
        theta = np.arcsin(d_z / length)
        t, x = self.fill_numerically(t, theta)
        x = x.reshape(-1)

        # roughly calculate the time it takes to fill through linear interpolation
        tau = np.interp(length, x, t)

        # calculate equivalent stats
        velocity_eq = length / tau
        length_eq = (self.d_h - d_z) / self.c / (velocity_eq ** 2)
        # print(f"height: {d_z}, length: {length}")
        # print(f"length: {length}, equivalent length: {length_eq}")
        # print()

        return length_eq
