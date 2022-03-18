from PipeConverter import PipeConverter
import argparse
from typing import Tuple, List
import matplotlib.pyplot as plt
from numpy import exp, log

"""
Ideally, we shouldn't have to use EPANET to calibrate our model (find the equivalent friction factors),
we should instead be able to use this method to iteratively calculate it
"""

# constants
g = 9.81
fpm = (2 / 3) ** 2  # flat pipe multiplier


def calculate_new_ff_log(length: float, diameter: float, pressure: float, tau: float) -> float:
    log_f = -3 * log(fpm * length) + 1.666666 * log(3 * tau / 2) + log(2 * diameter * g * pressure)
    return exp(log_f)


def calculate_new_ff(length: float, diameter: float, pressure: float, tau: float) -> float:
    return (1 / fpm / length * (3 * tau / 2 * ((2 * diameter * pressure * g) ** (1 / 2))) ** (2 / 3)) ** 3

    # see notes for derivation (this creates a lot of instability since the first term is VERY small)
    return ((1 / fpm / length) ** 3) * ((3 * tau / 2) ** 1.9) * 2 * diameter * pressure * g


def expectation_maximization(length: float, diameter: float, pressure: float, max_iterations: int = 4,
                             initial_f=0.02) -> Tuple[float, List[float]]:

    ff = initial_f
    all_ff = [ff]
    converter = PipeConverter()
    converter.update_pressure(pressure)
    for _ in range(max_iterations):
        print(ff)
        converter.f = ff
        # update tau
        tau = converter.fill_time(length, 0, diameter, update_pressure=False, update_f=False)
        print(f"{tau} [s]")
        print()
        # update and store ffs
        ff = calculate_new_ff(length, diameter, pressure, tau)
        all_ff.append(ff)

    return ff, all_ff


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--length", help="pipe length [m]", type=float)
    parser.add_argument("-d", "--diameter", help="pipe diameter [m]", type=float)
    parser.add_argument("-p", "--pressure", help="pressure head [m]", type=float)
    args = parser.parse_args()

    final_ff, all_ffs = expectation_maximization(args.length, args.diameter, args.pressure)
    print(f"Final friction factor is: {final_ff}")

    plt.plot(range(len(all_ffs)), all_ffs)
    plt.show()
