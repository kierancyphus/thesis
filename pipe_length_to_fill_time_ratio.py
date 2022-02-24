from PipeConverter import PipeConverter
import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple
from SimulationTimeGuesser import SimulationTimeGuesser


class PipeConverterExperimenter:
    def __init__(self, min_length: int = 10, max_length: int = 1000, min_height: int = 1, max_height: int = 10, diameter: float = 0.3) -> None:
        """
        Class to run experiments

        :param min_length: shortest pipe we want to investigate
        :param max_length: longest ---------------------------
        :param min_height: smallest change in height we want to investigate
        :param max_height: greatest -------------------------------------
        """

        self.min_length, self.max_length = min_length, max_length
        self.min_height, self.max_height = min_height, max_height
        self.diameter = diameter
        self.converter = PipeConverter()
        self.converter._calculate_c(diameter)

    def get_parameters(self) -> Tuple[np.ndarray, np.ndarray]:
        lengths = np.linspace(self.min_length, self.max_length, 20)
        heights = np.linspace(self.min_height, self.max_height, 10)
        return lengths, heights

    def constant_time(self, max_time: int = 180, num_points: int = 10000, plot: bool = True):
        """

        :param max_time: end time of pipe filling simulation
        :param num_points:
        :param plot:
        :return:
        """
        lengths, heights = self.get_parameters()

        t = np.linspace(0, max_time, num_points)
        for height in heights:
            # update pressure so that integration always succeeds
            self.converter.update_pressure(2 * height)

            fill_times = []
            for length in lengths:
                theta = np.arcsin(height / length)
                t, x = self.converter._fill_numerically(t, theta)
                x = x.reshape(-1)

                # roughly calculate the time it takes to fill through linear interpolation
                tau = np.interp(length, x, t)
                fill_times.append(tau)
                # fill_times.append(self.converter.equivalent_length(length, height) / length)
            if plot:
                plt.plot(lengths, fill_times, label=f"height: {height}")

        if plot:
            plt.plot(lengths, [max_time for _ in lengths], label=f"max time", color="black")
            plt.title(f'Constant time numerical integration; max_time: {max_time}')
            plt.xlabel("pipe length")
            plt.ylabel("Time (s)")
            plt.legend()
            plt.show()
        return

    def variable_time(self, num_points: int = 10000, plot: bool = True, type: str = "linear_length"):
        lengths, heights = self.get_parameters()

        # TODO: move this somewhere else
        offset = 100

        for height in heights:
            # update pressure so integration always succeeds
            self.converter.update_pressure(2 * height)
            fill_times = []
            for length in lengths:
                time = SimulationTimeGuesser(length, height, self.converter.c, offset, type).evaluate()
                # time = length

                t = np.linspace(0, time, num_points)
                theta = np.arcsin(height / length)
                t, x = self.converter._fill_numerically(t, theta)
                x = x.reshape(-1)

                # roughly calculate the time it takes to fill through linear interpolation
                tau = np.interp(length, x, t)
                fill_times.append(tau)
                # fill_times.append(self.converter.equivalent_length(length, height, time) / length)
            if plot:
                plt.plot(lengths, fill_times, label=f"height: {height}")

        if plot:
            plt.plot(lengths, [SimulationTimeGuesser(length, 0, self.converter.c, offset, type).evaluate() for length in lengths], label="max time", color="black")
            plt.title('Variable time integration window; max_time: length')
            plt.xlabel("pipe length")
            plt.ylabel("Time (s)")
            plt.legend()
            plt.show()
        return


if __name__ == "__main__":
    experimenter = PipeConverterExperimenter(10, 50000, 1, 10)
    # experimenter.constant_time()
    experimenter.variable_time(type="poly_length_offset")

    results = """
    The pipes seem to fill at a rate that is a function of the assumed pressure, height, and length of the pipe.
    Playing around with the parameters, it seems like length ** 1.45 + 200 reliably overestimates the total integration
    time by a small margin in the worst case.
    """