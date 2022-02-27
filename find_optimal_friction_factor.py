import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
from tqdm import tqdm
import os
import re
from glob import glob

from PipeConverter import PipeConverter
from WNTRWrapper import WNTRWrapper


def plot_all_ff(pipe_lengths, epanet_fill_times, friction_factors, simulation_fill_times_by_ff):
    # set seaborn theme
    sns.set_theme()

    # need to find max and min ff for scaling colours
    norm = matplotlib.colors.Normalize(vmin=np.min(friction_factors), vmax=np.max(friction_factors))

    for ff in friction_factors:
        simulation_fill_time = simulation_fill_times_by_ff[ff]
        plt.scatter(pipe_lengths, simulation_fill_time, alpha=0.5, c=[ff for _ in pipe_lengths], cmap="PuOr", norm=norm)

    plt.errorbar(pipe_lengths, epanet_fill_times, yerr=1.5, label="EPANET", color="black")
    plt.title('Pipe length [m] vs filling time [s] for various friction factors')
    plt.xlabel('Pipe length [m]')
    plt.ylabel('Time to fill [s]')
    cb = plt.colorbar()
    cb.set_label("Friction Factors")
    plt.legend()
    plt.show()


def plot_one_ff(pipe_lengths, epanet_fill_times, simulation_fill_time, best_ff):
    plt.errorbar(pipe_lengths, epanet_fill_times, yerr=1.5, label="EPANET", color="black")
    plt.scatter(pipe_lengths,
                simulation_fill_time,
                c=np.where(np.abs(epanet_fill_times - simulation_fill_time) <= 1.5, 'g', 'r'))  # in or out of range
    plt.title(f'Pipe length [m] vs filling time [s] for best friction factor = {best_ff:.4f}')
    plt.xlabel('Pipe length [m]')
    plt.ylabel('Time to fill [s]')
    plt.show()


def plot_percent_error(pipe_lengths, epanet_fill_times, simulation_fill_time, best_ff):
    plt.scatter(pipe_lengths,
                (epanet_fill_times - simulation_fill_time) / epanet_fill_times * 100,
                label=f"Deviation from EPANET for {best_ff:.4f}",
                alpha=0.5)
    plt.title(f'Percent difference from EPANET time vs filling time [s] for best friction factor = {best_ff:.4f}')
    plt.xlabel('Pipe length [m]')
    plt.ylabel('Percent difference from EPANET time')
    plt.show()


def get_difference(a: np.ndarray, b: np.ndarray, loss: str = "mse"):
    if loss == "hinge":
        return np.sum(np.abs(a - b))
    return np.sum((a - b) ** 2)


def create_and_run_epanet_simulation(length: float, diameter: float = 300, pressure: float = 20) -> float:
    """
    Creates an epanet file based on flat_template.inp
    :param length: pipe length
    :return: tau, time it takes for the pipe to fill
    """
    template_filepath = os.path.join(os.getcwd(), 'test_files', 'flat_template.inp')
    if not os.path.isfile(template_filepath):
        raise ValueError('Make sure that flat_template.inp is in the test_files folder')

    # create epanet file
    with open(template_filepath, 'r') as f:
        template = f.read()

    # replace length tag with actual length
    epanet_file = re.sub(r"<length>", str(length), template)
    epanet_file = re.sub(r"<diameter>", str(diameter * 1000), epanet_file)
    epanet_file = re.sub(r"<pressure>", str(pressure), epanet_file)

    # create reports folder if not exists
    if not os.path.exists('reports'):
        os.makedirs('reports')

    # save file
    epanet_file_path = os.path.join(os.getcwd(), 'reports', f"flat_pipe_length_{length}.inp")
    with open(epanet_file_path, 'w') as f:
        f.write(epanet_file)

    # # run simulations
    wrapper = WNTRWrapper(epanet_file_path, True)
    simulation_output_path = os.path.join(os.getcwd(), 'reports', f"flat_pipe_length_{length}")
    wrapper.run_sim(simulation_output_path)

    # parse report (only way to get good timestep)
    with open(simulation_output_path + ".rpt", 'r') as f:
        simulation_report = f.read()

    # cleanup
    for file in glob(os.path.join(os.getcwd(), 'reports', "*")):
        os.remove(file)

    # parse the report to find when the pipe opens (e.g. has filled)
    for line in simulation_report.splitlines():
        if "Pipe 7 changed from closed to open" in line:
            timestamp = line.strip().split(" ")[0]
            time_seconds = int(timestamp.split(":")[0]) * 60 * 60 + int(timestamp.split(":")[1]) * 60 + int(
                timestamp.split(":")[2])
            return time_seconds
    # should never get this but need a fallback if the flat pipe never fills
    return -1


def run_ff_simulations(pipe_lengths, friction_factors, pressure, diameter, loss):
    simulation_fill_times_by_ff = {ff: [] for ff in friction_factors}
    epanet_fill_times = []
    for length in tqdm(pipe_lengths, total=len(pipe_lengths)):
        # run epanet simulation
        # Note: for a flat pipe, the friction factor doesn't affect the pipe equivalent length since it is always 0.44
        epanet_fill_times.append(create_and_run_epanet_simulation(length, diameter, pressure))

        # run numerical integration for different ff
        for ff in friction_factors:
            converter = PipeConverter(f=ff)
            converter.update_pressure(pressure)
            fill_time = converter.fill_time(length, 0, diameter)
            simulation_fill_times_by_ff[ff].append(fill_time)

    # find the best ff value and plot compared to epanet (lowest loss)
    epanet_fill_times = np.array(epanet_fill_times)
    differences = []
    for ff, result in simulation_fill_times_by_ff.items():
        differences.append((get_difference(epanet_fill_times, np.array(result), loss=loss), ff))

    _, best_ff_index = sorted(differences, key=lambda tup: tup[0])[0]

    return epanet_fill_times, simulation_fill_times_by_ff, best_ff_index


def process_bucket(lower_bound, upper_bound, num_length_samples, friction_factors, pressure, diameter, loss):
    pipe_lengths = list(np.linspace(lower_bound, upper_bound, num_length_samples))
    epanet_fill_times, simulation_fill_times_by_ff, best_ff = run_ff_simulations(pipe_lengths, friction_factors,
                                                                                 pressure, diameter, loss)
    simulation_fill_times = simulation_fill_times_by_ff[best_ff]
    best_mse = get_difference(epanet_fill_times, simulation_fill_times)
    percent_points_within_bounds = np.sum(
        np.where(np.abs(epanet_fill_times - simulation_fill_times) <= 1.5, 1, 0)) / num_length_samples * 100
    percent_deviations = (epanet_fill_times - simulation_fill_times) / epanet_fill_times * 100
    result_string = "\t".join([f"[{lower_bound}, {upper_bound}]", f"{best_ff:.4f}", f"{best_mse:.4f}",
                               f"{percent_points_within_bounds}",
                               f"[{np.min(percent_deviations):.2f}, {np.max(percent_deviations):.2f}]"])
    return result_string


def get_ideal_ff_per_bucket():
    num_length_samples = 10
    num_friction_factor_samples = 100
    pressure = 20
    diameter = 0.3
    loss = "mse"

    friction_factors = np.linspace(0.02, 0.05, num_friction_factor_samples)

    results = []
    results.append("\t".join(["Range", "Friction Factor", "MSE", "% in Bounds", "% Deviation Range"]))
    # [100, 8000]
    for i in range(1, 80):
        lower_bound, upper_bound = i * 100 + 1,  i * 100 + 101
        result_string = process_bucket(lower_bound, upper_bound, num_length_samples, friction_factors, pressure, diameter, loss)
        results.append(result_string)

    # # [1000, 5000] upper and lower bounds empirically chosen
    # friction_factors = np.linspace(0.027, 0.031, num_friction_factor_samples)
    # for i in range(20):
    #     lower_bound, upper_bound = i * 200 + 1000, i * 200 + 1200
    #     result_string = process_bucket(lower_bound, upper_bound, num_length_samples, friction_factors, pressure,
    #                                    diameter, loss)
    #     results.append(result_string)
    #
    # # [5000, 8000] upper and lower bounds empirically chosen
    # friction_factors = np.linspace(0.03, 0.035, num_friction_factor_samples)
    # for i in range(6):
    #     lower_bound, upper_bound = i * 500 + 5000, i * 500 + 5500
    #     result_string = process_bucket(lower_bound, upper_bound, num_length_samples, friction_factors, pressure,
    #                                    diameter, loss)
    #     results.append(result_string)

    for result in results:
        print(result)


def run_experiments():
    pipe_lengths = list(np.linspace(1000, 1100, 20))
    friction_factors = np.linspace(0.005, 0.05, 50)

    # default params are pressure head of 20 and 300mm diameter
    pressure = 20
    diameter = 0.3
    loss = "mse"

    epanet_fill_times, simulation_fill_times_by_ff, best_ff = run_ff_simulations(pipe_lengths, friction_factors,
                                                                                       pressure, diameter, loss)
    ## Plotting
    # Loss vs friction factor
    plot_all_ff(pipe_lengths, epanet_fill_times, friction_factors, simulation_fill_times_by_ff)

    # EPANET vs simulation filling time for best ff value
    plot_one_ff(pipe_lengths, epanet_fill_times, simulation_fill_times_by_ff[best_ff], best_ff)

    # plot differential compared to error bars
    plot_percent_error(pipe_lengths, epanet_fill_times, simulation_fill_times_by_ff[best_ff], best_ff)


if __name__ == "__main__":
    run_experiments()
    # get_ideal_ff_per_bucket()
    """
    Discussion:
    Using MSE chooses an ff value that fits better for later values since they are likely to deviate more and
    dominate the sum. Hinge loss might be better.
    ff in np.linspace(0.01, 0.1, 30)
    
    MSE
    range:      diameter    ff      in_range    % range from EPANET
    100-200:    0.3         0.026   All         [-0.4, 2.0]
    100-400:    0.3         0.0255  All         [-9, 1]
    100-500:    0.3         0.029   -1
    100-1000:   0.3         0.029   +1
    400-500:    0.3         0.026   -4          [0.4, 2]
    100-7000:   0.3         0.0317  +1          [-22, 0]
    
    # Looks like the friction factors are proportional to the size of the diameter?
    100-400:    1           0.0845  All         [-9, 1]
    100-400:    0.1         0.0089  All         [-11, -1]
    
    TODO: I read the wikipedia article and it said that the friction factor changes as a function of the diameter
    but it looks like it also changes as a function of length. Here is what I need to do next.
    - Experiment for different pipe length ranges of 100m, up to 10km
        - I'm expecting that for long pipes the effects start to drop off and so we can bin those buckets together
    - Experiment for different pipe diameters, from 0.1m to 5m
        - Expecting the same sort of behaviour as above
    - Experiment for different pipe roughnesses (in EPANET) and see how that translates in ff
        - Also should read up on what they actually do internally
    
    Ideally, I can create a 3D lookup table that allows me to choose a friction factor such that the EPANET and modelled
    scenarios align to within +-1.5% (or some other small number). For short pipes, getting them to align within the
    uncertainty would also be great.
    
    """
