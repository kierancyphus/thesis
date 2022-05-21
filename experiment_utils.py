import os
import re
from glob import glob
import yaml
from typing import Dict, Tuple

from WNTRWrapper import WNTRWrapper
from ModificationStrategy import Strategy


def parse_line_time(line: str):
    timestamp = line.strip().split(" ")[0]
    time_seconds = int(timestamp.split(":")[0]) * 60 * 60 + int(timestamp.split(":")[1]) * 60 + int(
        timestamp.split(":")[2])
    return time_seconds


def create_epanet_file(length: float, diameter: float = 300, pressure: float = 20, roughness: float = 100,
                       height: float = 10, template_prefix: str = 'flat_template.inp') -> str:
    """
    Populates the template at the prefix with the following values

    :param length: m
    :param diameter: mm
    :param pressure: m
    :param roughness: something
    :param height: m
    :param template_prefix: str
    :return: the modified template file as a str
    """
    template_filepath = os.path.join(os.getcwd(), 'test_files', template_prefix)
    if not os.path.isfile(template_filepath):
        raise ValueError('Make sure that flat_template.inp is in the test_files folder')

    # create epanet file
    with open(template_filepath, 'r') as f:
        template = f.read()

    # replace length tag with actual length
    epanet_file = re.sub(r"<length>", str(length), template)
    epanet_file = re.sub(r"<diameter>", str(diameter * 1000), epanet_file)
    epanet_file = re.sub(r"<pressure>", str(pressure), epanet_file)
    epanet_file = re.sub(r"<roughness>", str(roughness), epanet_file)
    epanet_file = re.sub(f"<height>", str(height), epanet_file)

    return epanet_file


def save_epanet_file_yaml(epanet_file: str, yaml_file: str, template_prefix: str) -> str:
    # create reports folder if not exists
    if not os.path.exists('reports'):
        os.makedirs('reports')

    # save file
    epanet_file_path = os.path.join(os.getcwd(), 'reports', f"{template_prefix[:-4]}_{yaml_file[:-4]}.inp")
    with open(epanet_file_path, 'w') as f:
        f.write(epanet_file)

    return epanet_file_path


def save_epanet_file(epanet_file: str, length: float, diameter: float, pressure: float,
                     roughness: float, height: float, template_prefix: str) -> str:
    # create reports folder if not exists
    if not os.path.exists('reports'):
        os.makedirs('reports')

    # save file
    epanet_file_path = os.path.join(os.getcwd(), 'reports',
                                    f"{template_prefix[:-4]}_{length}_{diameter}_{pressure}_{roughness}_{height}.inp")
    with open(epanet_file_path, 'w') as f:
        f.write(epanet_file)

    return epanet_file_path


def create_and_run_epanet_simulation(length: float, diameter: float = 300, pressure: float = 20,
                                     roughness: float = 100, height: float = 10, template_prefix: str = 'flat_template.inp',
                                     strategy=Strategy.SINGLE_TANK_CV, tank_height_multiplier: float = 1,
                                     cf: float = 1, search_string: str = "Pipe 7 changed from closed to open") -> float:
    """
    Creates an epanet file based on flat_template.inp
    :param length: pipe length
    :return: tau, time it takes for the pipe to fill
    """
    epanet_file = create_epanet_file(length, diameter, pressure, roughness, height, template_prefix)

    epanet_file_path = save_epanet_file(epanet_file, length, diameter, pressure, roughness, height, template_prefix)

    # run simulations
    wrapper = WNTRWrapper(epanet_file_path, is_iwn=True, strategy=strategy,
                          tank_height_multiplier=tank_height_multiplier,
                          cf=cf)
    simulation_output_path = os.path.join(os.getcwd(), 'reports', epanet_file_path[:-4])
    wrapper.run_sim(simulation_output_path)

    # parse report (only way to get good timestep)
    with open(simulation_output_path + ".rpt", 'r') as f:
        simulation_report = f.read()

    # cleanup
    for file in glob(os.path.join(os.getcwd(), 'reports', "*")):
        os.remove(file)

    # parse the report to find when the pipe opens (e.g. has filled)
    for line in simulation_report.splitlines():
        if search_string in line:
            return parse_line_time(line)
    # should never get this but need a fallback if the flat pipe never fills
    return -1


def populate_final_template(template_path: str, config_path: str) -> Tuple[str, any]:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    with open(template_path, 'r') as f:
        template = f.read()

    # populate junctions
    for i in range(1, 12):
        template = re.sub(rf"<e{i}>", str(config["pipes"]["elevation"][i - 1]), template)

    # update reservoir elevations
    template = re.sub(r"<e0>", str(config["reservoirs"]["elevation"][0]), template)
    template = re.sub(r"<e12>", str(config["reservoirs"]["elevation"][1]), template)

    # populate pipes
    for i in range(12):
        template = re.sub(rf"<l{i}>", str(config["pipes"]["length"][i]), template)
        template = re.sub(rf"<d{i}>", str(config["pipes"]["diameter"][i]), template)

    return template, config


def create_and_run_final_simulation(template_prefix: str = "results_template.inp", config_prefix: str = "uphill.yaml") -> Dict[int, int]:
    # update filepaths
    template_filepath = os.path.join(os.getcwd(), 'test_files', template_prefix)
    config_filepath = os.path.join(os.getcwd(), 'test_files', config_prefix)

    epanet_file, config = populate_final_template(template_filepath, config_filepath)
    epanet_file_path = save_epanet_file_yaml(epanet_file, config_prefix, template_prefix)

    # run simulations
    wrapper = WNTRWrapper(epanet_file_path, is_iwn=True)
    simulation_output_path = os.path.join(os.getcwd(), 'reports', epanet_file_path[:-4])
    wrapper.run_sim(simulation_output_path)

    # parse report (only way to get good timestep)
    with open(simulation_output_path + ".rpt", 'r') as f:
        simulation_report = f.read()

    # cleanup
    for file in glob(os.path.join(os.getcwd(), 'reports', "*")):
        os.remove(file)

    # parse the report to find when each rule is completed (breaks if pipe never fills :()
    filling_front_times = {}
    # calculate the location of the filling front
    pipe_distances = [sum(config["pipes"]["length"][:i + 1]) for i in range(len(config["pipes"]["length"]))]
    for line in simulation_report.splitlines():
        for i in range(1, 11):
            if pipe_distances[i] not in filling_front_times.keys() and f"rule {i}" in line:
                filling_front_times[pipe_distances[i]] = parse_line_time(line)

    return filling_front_times


if __name__ == "__main__":
    times = create_and_run_final_simulation()
    print(times)
