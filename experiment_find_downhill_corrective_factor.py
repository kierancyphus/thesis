from experiment_effects_of_height import run_down_simulation
from experiment_find_optimal_friction_factor import get_difference, plot_all
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns


def find_cf(heights, pipe_length, diameter, pressure, roughness, corrective_factors, thm: float = 1):
    _, simulation_fill_times = run_down_simulation(heights, pipe_length, diameter, pressure, roughness,
                                                   thm=thm,
                                                   include_epanet=False)

    epanet_fill_times_by_cf = {}
    for cf in tqdm(corrective_factors, total=len(corrective_factors)):
        epanet_fill_times, _ = run_down_simulation(heights, pipe_length, diameter, pressure, roughness,
                                                   cf=cf,
                                                   thm=thm,
                                                   include_num=False,
                                                   show_progress=False)
        epanet_fill_times_by_cf[cf] = epanet_fill_times

    # find the best ff value and plot compared to epanet (lowest loss)
    simulation_fill_times = np.array(simulation_fill_times)
    differences = []
    for cf, result in epanet_fill_times_by_cf.items():
        differences.append((get_difference(simulation_fill_times, np.array(result)), cf))

    _, best_cf_index = sorted(differences, key=lambda tup: tup[0])[0]

    return simulation_fill_times, epanet_fill_times_by_cf, best_cf_index


if __name__ == "__main__":
    heights = np.linspace(0.5, 60, 30)
    corrective_factors = np.linspace(1, 1.2, 5)
    pipe_length = 1000
    diameter = 0.3
    pressure = 20
    roughness = 100
    # tank_height_multiplier = 0.8103 # 0.9310
    tank_height_multiplier = 0.6897

    simulation_fill_times, epanet_fill_times_by_cf, best_cf_index = find_cf(heights, pipe_length, diameter, pressure,
                                                                            roughness, corrective_factors,
                                                                            thm=tank_height_multiplier)

    plot_all(heights, simulation_fill_times, corrective_factors, epanet_fill_times_by_cf, best_cf_index,
             "Drop in height [m]", "cf")

    epanet_fill_times_matrix = np.array(list(epanet_fill_times_by_cf.values()))
    print(epanet_fill_times_matrix)
    print()
    diff_matrix = np.abs(epanet_fill_times_matrix - simulation_fill_times)
    print(diff_matrix)
    print()
    mins = np.argmin(diff_matrix, axis=1)
    print(mins)
    print()
    heights_for_cf = heights[mins]
    print(heights_for_cf)
    print()
    plt.scatter(heights_for_cf, corrective_factors)
    plt.show()

    # palette = sns.color_palette('coolwarm')
    # sns.set_theme(palette=palette)
    # yerr = 3
    #
    # plt.errorbar(heights, epanet_fill_times, yerr=yerr, label="EPANET", color="black", fmt="o", alpha=0.75, capsize=2)
    # plt.scatter(heights,
    #             simulation_fill_times,
    #             alpha=0.5,
    #             c=np.where(np.abs(epanet_fill_times - simulation_fill_times) <= yerr, 'g', 'r'))  # in or out of range
    # plt.legend(["Simulation", "EPANET"])
    # plt.title(f'Filling time [s] vs Elevation [m] for 1km Pipe')
    # plt.xlabel('Pipe elevation [m]')
    # plt.ylabel('Time to fill [s]')
    # plt.show()
