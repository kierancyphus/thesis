from PipeConverter import PipeConverter
import argparse
from typing import Union
import matplotlib.pyplot as plt
from experiment_utils import create_and_run_final_simulation

"""
Note I manually did this the first time and the calculated times for epanet were
    plt.scatter([318, 918, 1722, 2688], [1000, 2000, 3000, 4000], c='r', alpha=0.5)
"""


def plot_final_graph(x, t, epanet_x, epanet_t) -> None:
    # // 2 is just because the numerical simulation goes on a while
    plt.plot(t[:len(t) // 2], x[:len(x) // 2])
    plt.scatter(epanet_t, epanet_x, c='r', alpha=0.5)
    plt.legend(['Mathematical filling front', 'EPANET filling front'])
    plt.xlabel('Time [s]')
    plt.ylabel('Location of filling front [m]')
    plt.title('Location of filling front [m] vs Time [s]')
    plt.show()
    return


def get_numerical_time(args):
    converter = PipeConverter()
    # consider the flat pipe case
    pressure = args.elevation * 2 if args.pressure is None else args.pressure
    converter.update_pressure(pressure)
    tau, t, x = converter.fill_time(args.length, args.elevation, args.diameter, update_pressure=False,
                                    return_fronts=True)
    return tau, t, x


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--length", help="pipe length [m]", type=float)
    parser.add_argument("-d", "--diameter", help="pipe diameter [m]", type=float)
    parser.add_argument("-e", "--elevation", help="change in height [m]", type=float)
    parser.add_argument("-p", "--pressure", help="pressure head [m]", type=float)
    parser.add_argument("-c", "--config", help="Name of config file", type=str)
    parser.add_argument("-t", "--template", help="path to template file", type=str)
    args = parser.parse_args()

    tau, t, x = get_numerical_time(args)
    filling_front_times = create_and_run_final_simulation(config_prefix=args.config if args.config is not None else "uphill.yaml")

    plot_final_graph(x, t, filling_front_times.keys(), filling_front_times.values())
