import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt
from IPipe import IPipe
from typing import Tuple, List


class Pipe(IPipe):
    def get_equivalent_length(self) -> float:
        pass

    def fill_numerically(self, t: np.ndarray, plot=False) -> Tuple[np.ndarray, np.ndarray]:
        def derivative(x, t, delta_h, c, theta):
            deriv = np.sqrt(delta_h / c / x - np.sin(theta) / c)
            # print(f"derivative at time t: {t} is {deriv}")
            return deriv

        # set to be really small number so we don't get divide by 0 errors
        x: np.ndarray = odeint(derivative, 1e-7, t, args=(self.delta_h, self.c, self.theta))

        if plot:
            print("Plotting...")
            plt.plot(t, x, 'r')
            # plt.plot(t, t, 'b', label="initial velocity")
            plt.xlabel('time')
            plt.ylabel('position of water front')
            plt.legend()
            plt.title("Position of water front over time")
            plt.show()

        return t, x

    def plot_flat_vs_angled(self, t: np.ndarray):
        t_angled, x_angled = self.fill_numerically(t, False)
        x_angled = x_angled.reshape(-1)

        constant = (9 / 4 * self.delta_h / self.c) ** (1 / 3)
        t_flat, x_flat = t, t ** (2 / 3) * constant

        # print(x_flat.shape, x_angled.shape)
        # print(x_flat - x_angled)

        plt.plot(t_angled, x_angled, 'r', label="angled")
        plt.plot(t_angled, x_flat, 'b', label="flat")
        plt.plot(t, np.abs(x_flat - x_angled), 'g', label="difference")
        plt.xlabel('time')
        plt.ylabel('position of water front')
        plt.legend()
        plt.title("Position of water front over time")
        plt.show()

    def numerically_calculate_equivalent_length(self, should_print=False, constant_slope=False) -> Tuple[float, float, float, float]:
        """
        Calculate the equivalent pipe length given the original length, c, angle of incline,
        and change in head.
        Assume that the pipe doesn't take longer than 3 minutes to fill.

        :return: tuple of original pipe length, equivalent length, original incline, equivalent incline
        """
        # numerically fill pipe
        # Note: There is a lot of numerical instability here and we might have to sample a lot of points to get decent
        # results. Also need to test with reasonable numbers
        t = np.linspace(0, 3 * 60, 10000)
        t, x = self.fill_numerically(t, False)
        x = x.reshape(-1)

        # roughly calculate the time it takes to fill through linear interpolation
        tau = np.interp(self.length, x, t)

        # calculate equivalent stats
        velocity_eq = self.length / tau
        if constant_slope:
            length_eq = self.delta_h / (np.sin(self.theta) + self.c * (velocity_eq ** 2))
        else:
            length_eq = (self.delta_h - self.delta_z) / self.c / (velocity_eq ** 2)

        theta_eq = np.arcsin(self.delta_z / length_eq)
        if should_print:
            print(f"delta_h: {self.delta_h}, c: {self.c}, theta_o: {self.theta}, length_o: {self.length}, theta_e: "
                  f"{theta_eq}, length_eq: {length_eq}")

        return self.length, length_eq, self.theta, theta_eq


class Experimenter:
    def __init__(self, lengths: np.ndarray, thetas: np.ndarray, heads: np.ndarray = np.array([10.]), cs: List[float] = [1]):
        """
        Warnings are fine since init is only run once

        :param lengths: list of original lengths
        :param thetas: list of different angles
        :return: nothing, but it plots the effect of different angles and original lengths and prints info
        """
        self.lengths = lengths
        self.thetas = thetas
        self.heads = heads
        self.cs = cs

    def run_numerical_experiments(self, delta_h=10, c=1, default_length=10, should_print=False, constant_slope=False):
        flat_equivalent = (2 / 3) ** 2

        l_eqs = [[Pipe(delta_h, c, theta, default_length).numerically_calculate_equivalent_length(should_print, constant_slope)[1] for theta in
                  self.thetas] for delta_h in self.heads]

        plt.plot(self.thetas, [flat_equivalent for _ in self.thetas], 'b', label="flat pipe equivalent")

        for index, delta_h in enumerate(self.heads):
            plt.plot(self.thetas, np.array(l_eqs[index]) / default_length, label=f"head: {delta_h:.1f}m")

        plt.xlabel('angle (radians)')
        plt.ylabel('equivalent length (m)')
        plt.legend()
        plt.title(f"Equivalent length vs Angle Incline")
        fig = plt.gcf()
        fig.set_size_inches(12, 10)
        plt.savefig('results/length_vs_angle.jpg', dpi=100)
        plt.show()

        zs = [np.sin(theta) * default_length for theta in self.thetas]

        plt.plot(zs, [flat_equivalent for _ in self.thetas], 'b', label="flat pipe equivalent")

        for index, delta_h in enumerate(self.heads):
            plt.plot(zs, np.array(l_eqs[index]) / default_length, label=f"head: {delta_h:.1f}m")

        plt.xlabel('Change in Height (m)')
        plt.ylabel('Equivalent Length (m)')
        plt.legend()
        plt.title(f"Equivalent Length vs Change in Height")
        fig = plt.gcf()
        fig.set_size_inches(12, 10)
        plt.savefig('results/length_vs_height.jpg', dpi=100)
        plt.show()

        """
        Want to find something that shows the equivalent length as a function of the ratio of head vs z
        """

        plt.plot(zs, [flat_equivalent for _ in self.thetas], 'b', label="flat pipe equivalent")

        for index, delta_h in enumerate(self.heads):
            plt.plot(np.array(zs) / delta_h, np.array(l_eqs[index]) / default_length, label=f"head: {delta_h:.1f}m")

        plt.xlabel('Change in height / Pressure Head')
        plt.ylabel('Equivalent Length (m)')
        plt.legend()
        plt.title(f"Equivalent Length vs Pressure / Height Ratio")
        fig = plt.gcf()
        fig.set_size_inches(12, 10)
        plt.savefig('results/length_vs_ratio.jpg', dpi=100)
        plt.show()

        # l_eq_thetas, theta_eq_thetas = [], []
        # for theta in self.thetas:
        #     _, l_eq, _, theta_eq = Pipe(delta_h, c, theta, default_length).numerically_calculate_equivalent_length()
        #     l_eq_thetas.append(l_eq)
        #     theta_eq_thetas.append(theta_eq)
        #
        # plt.plot(self.thetas, np.array(l_eq_thetas) / default_length, 'r', label="equivalent pipe length")
        # plt.plot(self.thetas, [flat_equivalent for _ in self.thetas], 'b', label="flat pipe equivalent")
        # plt.xlabel('angle (radians)')
        # plt.ylabel('equivalent length (m)')
        # plt.legend()
        # plt.title("Equivalent length vs angle incline")
        # plt.show()
        #
        # plt.plot(self.thetas, theta_eq_thetas, 'r', label="equivalent angle")
        # plt.xlabel('angle (radians)')
        # plt.ylabel('equivalent angle (radians)')
        # plt.legend()
        # plt.title("Equivalent angle vs original angle incline")
        # plt.show()
