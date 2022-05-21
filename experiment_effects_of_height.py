from experiment_utils import create_and_run_epanet_simulation
from PipeConverter import PipeConverter
from ModificationStrategy import Strategy
from tqdm import tqdm
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


def numerical_integration(pressure, pipe_length, height, diameter, constant_pressure=True):
    converter = PipeConverter()
    converter.update_pressure(pressure)
    return converter.fill_time(pipe_length, height, diameter, update_pressure=not constant_pressure)


def run_up_simulation(heights, pipe_length, diameter, pressure, roughness, thm: float = 1, include_epanet=True,
                      include_num=True, constant_pressure=True):
    template_filepath = "up_template.inp"
    strategy = Strategy.SINGLE_TANK_CV_CONSTANT_PRESSURE if constant_pressure else Strategy.SINGLE_TANK_CV

    epanet_fill_times, simulation_fill_times = [], []
    for height in tqdm(heights, total=len(heights)):
        # run epanet simulation
        # Note: for a flat pipe, the friction factor doesn't affect the pipe equivalent length since it is always 0.44
        if include_epanet:
            epanet_fill_times.append(
                create_and_run_epanet_simulation(pipe_length, diameter, pressure, roughness, height, template_filepath,
                                                 strategy=strategy,
                                                 tank_height_multiplier=thm))

        # run numerical integration
        if include_num:
            simulation_fill_times.append(
                numerical_integration(pressure, pipe_length, height, diameter, constant_pressure=constant_pressure))

    return epanet_fill_times, simulation_fill_times


def run_down_simulation(heights, pipe_length, diameter, pressure, roughness, thm: float = 1, cf: float = 1,
                        include_epanet: bool = True,
                        include_num: bool = True,
                        show_progress: bool = True,
                        constant_pressure: bool = True):
    template_filepath = "down_template.inp"
    strategy = Strategy.SINGLE_TANK_CV_CONSTANT_PRESSURE if constant_pressure else Strategy.SINGLE_TANK_CV

    epanet_fill_times, simulation_fill_times = [], []

    iterator = tqdm(heights, total=len(heights)) if show_progress else heights
    for height in iterator:
        # note that for a downwards sloping pipe, the "pressure" should actually be pressure + height to make
        # sure the epanet simulation is the same as numerical

        # run epanet simulation
        if include_epanet:
            epanet_fill_times.append(
                create_and_run_epanet_simulation(pipe_length, diameter, pressure + height, roughness, height,
                                                 template_filepath,
                                                 strategy=strategy,
                                                 tank_height_multiplier=thm,
                                                 cf=cf))

        # run numerical integration
        if include_num:
            simulation_fill_times.append(
                numerical_integration(pressure, pipe_length, -height, diameter, constant_pressure=constant_pressure))

    return epanet_fill_times, simulation_fill_times


def run_up_down_simulation(heights, pipe_length, diameter, pressure, roughness, thm: float = 1, cf: float = 1,
                           include_epanet=True,
                           include_num=True, constant_pressure=True):
    # upwards sloping pipe
    epanet_fill_times_up, simulation_fill_times_up = run_up_simulation(heights, pipe_length, diameter, pressure,
                                                                       roughness,
                                                                       thm=thm,
                                                                       include_epanet=include_epanet,
                                                                       include_num=include_num,
                                                                       constant_pressure=constant_pressure)

    epanet_fill_times_up = np.array(epanet_fill_times_up)

    # downward sloping pipe
    epanet_fill_times_down, simulation_fill_times_down = run_down_simulation(heights, pipe_length, diameter, pressure,
                                                                             roughness,
                                                                             thm=thm,
                                                                             cf=cf,
                                                                             include_epanet=include_epanet,
                                                                             include_num=include_num,
                                                                             constant_pressure=constant_pressure)
    heights_down = heights * -1
    epanet_fill_times_down = np.array(epanet_fill_times_down)

    # combining
    heights = list(heights_down) + list(heights)
    epanet_fill_times = np.array(list(epanet_fill_times_down) + list(epanet_fill_times_up))
    simulation_fill_times = np.array(list(simulation_fill_times_down) + list(simulation_fill_times_up))
    return heights, epanet_fill_times, simulation_fill_times


if __name__ == "__main__":
    constant_pressure = True
    plot_epanet = True
    heights = np.linspace(0, 10, 20)
    pipe_length = 1000
    diameter = 0.3
    pressure = 20
    roughness = 100
    tank_height_multiplier = 0.6897

    heights, epanet_fill_times, simulation_fill_times = run_up_down_simulation(heights, pipe_length, diameter, pressure,
                                                                               roughness, thm=tank_height_multiplier,
                                                                               constant_pressure=constant_pressure)

    palette = sns.color_palette('coolwarm')
    sns.set_theme(palette=palette)
    yerr = 3

    if plot_epanet:
        plt.scatter(heights, simulation_fill_times, alpha=0.5,
                    c=np.where(np.abs(epanet_fill_times - simulation_fill_times) <= yerr, 'g', 'r'))  # within range

        plt.errorbar(heights, epanet_fill_times, yerr=yerr, label="EPANET", color="black", fmt="o", alpha=0.5,
                     capsize=2)
        plt.legend(["Simulation", "EPANET"])

    else:
        plt.scatter(heights, simulation_fill_times)

    plt.title(f'Filling time [s] vs Elevation [m] for 1km Pipe')
    plt.xlabel('Pipe elevation [m]')
    plt.ylabel('Time to fill [s]')
    plt.show()
