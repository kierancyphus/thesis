from PipeConverter import PipeConverter
from typing import List, Dict, Union, Tuple
import numpy as np


class FileParser:
    def __init__(self, file_path: str, converter: PipeConverter) -> None:
        self.file_path = file_path
        with open(file_path, 'r+') as file:
            self.file = file.read().splitlines()

        self.headers = self.get_headers()
        self.content = self.get_content()

        # check that the file is valid
        if not self.valid_input():
            raise ValueError(
                'Error: Please ensure that you are selecting a valid .inp file with a RULES, TANKS, and PIPES section')

        # should add comment or not
        self.added_pipe = False
        self.added_tank = False
        self.added_rule = False
        self.comment = ";Automated content below - Do not edit!"

        # next available id
        self.rule_count = self.get_rule_count()

        # converter for calculating equivalent lengths
        self.pressure = self.calculate_required_pressure()
        self.converter = converter
        self.converter.update_pressure(self.pressure)

    def calculate_required_pressure(self) -> float:
        """
        Determines the range in elevation of the network and then assumes that there is twice that much pressure in
        the system
        :return:
        """
        lowest = highest = 0
        for element in ("JUNCTIONS", "TANKS", "RESERVOIRS"):
            for junction in self.content[element]:
                if self.is_comment(junction):
                    continue
                elevation = float(junction.split("\t")[1].strip())
                lowest = min(lowest, elevation)
                highest = max(highest, elevation)
        return 1 if highest - lowest <= 0 else 2 * (highest - lowest)

    def valid_input(self):
        return "TANKS" in self.headers and "PIPES" in self.headers and "RULES" in self.headers

    @staticmethod
    def is_comment(string: str) -> bool:
        return string.strip()[0] == ";"

    def get_headers(self) -> List[str]:
        headers = []
        for line in self.file:
            stripped_line = line.strip()
            if len(stripped_line) > 0:
                if stripped_line[0] == "[" and stripped_line[-1] == "]":
                    headers.append(line[1: -1])
        return headers

    def get_content(self) -> Dict[str, List[str]]:
        # returns a dict mapping section to content lines
        content_dict = {}
        accum = []
        current = ""
        for line in self.file:
            if len(line) > 0:
                # if this is a header (eliminates whitespace)
                if line.strip()[1: -1] in self.headers:
                    # skip first case
                    if len(current) > 0:
                        content_dict[current] = accum
                        accum = []
                    current = line[1: -1]
                    continue
                accum.append(line)
        return content_dict

    def get_rule_count(self) -> int:
        current = 0
        for line in self.content["RULES"]:
            if "RULE" in line:
                current += 1
        return current + 1

    def reconstruct_file(self) -> str:
        file = ""
        for header, content in self.content.items():
            file += f"[{header}]\n"
            for line in content:
                file += line + "\n"
            file += "\n"
        file += "[END]\n"
        return file

    def add_rule(self, tank_id: str, tank_level, pipe_id: str) -> Union[str, int]:
        # TODO: abstract this to a check comment method that takes in the section name
        if not self.added_rule:
            self.added_rule = True
            self.content["RULES"].append(self.comment)
        # create rule s.t. it's triggered when level is above 99% of tank capacity
        rule = f"RULE\t{self.rule_count}\nIF\tTANK\t{tank_id}\tLEVEL\tABOVE\t{tank_level * 0.99}\nTHEN\tPIPE\t{pipe_id}\tSTATUS\tIS\tOPEN\n\n "
        self.rule_count += 1
        self.content["RULES"].append(rule)
        return self.rule_count - 1

    def add_tank(self, id: str, elevation: int, max_level: int, diameter: Union[float, int], init_level: int = 0,
                 min_level: int = 0, min_vol: int = 0) -> str:
        # init level, min level and min volume should always be zero, max level
        # Diameter and max level are calculated from volume
        # TODO: calculate coordinates and add them
        if not self.added_tank:
            self.added_tank = True
            self.content["TANKS"].append(self.comment)

        tank = "\t".join(
            [str(x) for x in [id, elevation, init_level, min_level, max_level, diameter, min_vol, "", ";"]])
        self.content["TANKS"].append(tank)
        return id

    def add_pipe(self, node_a: Union[str, int], node_b: Union[str, int], length: Union[str, int, float],
                 diameter: Union[str, int], status: str = "Open") -> str:
        """
        Used for adding shadow pipes - the id will always be f"{node_a}->{node_b}".
        It might visually look a bit different, but when you upload the model it strips whitespace, so the tabs are important here

        Roughness and Minor loss are both set to be 0
        :param status: Optional status; used for to say if pipe has a check valve or not
        :param node_a:
        :param node_b:
        :param length:
        :param diameter:
        :return:
        """
        if not self.added_pipe:
            self.added_pipe = True
            self.content["PIPES"].append(self.comment)

        node_a_id = f"({node_a})" if "->" in node_a else node_a
        node_b_id = f"({node_b})" if "->" in node_b else node_b

        pipe = "\t".join(
            [str(x) for x in [f"{node_a_id}->{node_b_id}", node_a, node_b, length, diameter, 100, 0, status, ";"]])
        self.content["PIPES"].append(pipe)
        return f"{node_a}__{node_b}"

    def add_psv(self, node_origin: Union[str, int], node_dest: Union[str, int]) -> Tuple[
        Union[str, int], Union[str, int]]:
        # create junction to attach PSV
        psv_start, psv_end = f"{node_origin}->{node_dest}" + "_psv", f"{node_origin}->{node_dest}" + "_psv_end"
        psv_elevation = str(self.get_elevation(node_origin))
        # TODO: check what demand should be
        psv_junction = "\t".join([psv_start, psv_elevation, "0", "", ";"])
        psv_junction_end = "\t".join([psv_end, psv_elevation, "0", "", ";"])
        self.content["JUNCTIONS"].append(psv_junction)
        self.content["JUNCTIONS"].append(psv_junction_end)

        # attach PSV
        psv_valve = "\t".join([f"{node_origin}->{node_dest}" + "_psv_pipe",  # pipe id
                               psv_start,  # start
                               psv_end,  # end
                               "100",  # TODO: update diameter (I think this is cm)
                               "PSV",  # type of valve
                               str(self.pressure),  # pressure to be sustained
                               "0",  # minor loss
                               ";"])
        self.content["VALVES"].append(psv_valve)
        return psv_start, psv_end

    def set_initial_pipes_closed(self):
        for index, pipe in enumerate(self.content["PIPES"]):
            if self.is_comment(pipe):
                continue
            pipe_split = pipe.split("\t")
            # Status column should always be the 8th
            pipe_split[7] = "Closed"
            self.content["PIPES"][index] = "\t".join(pipe_split)

    def get_elevation(self, node: str) -> int:
        # need to check [JUNCTIONS] [RESERVOIRS] [TANKS]
        for element in ("JUNCTIONS", "TANKS", "RESERVOIRS"):
            for junction in self.content[element]:
                junction_params = junction.split("\t")
                if junction_params[0].strip() == node:
                    return int(junction_params[1])

        raise Exception(f"Error: There is no tank or junction called: {node}")

    def parse_pipe(self, pipe: str) -> Tuple[str, str, str, float, Union[int, float], int, int, float, float]:
        """
        Returns useful values about the pipe. Note: node_a is always the pipe with the lower elevation
        :param pipe: row from the parsed file
        :return: id, node_a, node_b, length, diameter, d_z, elevation_min, volume, diameter_equivalent
        """
        pipe_split = pipe.split('\t')
        pipe_id, node_a, node_b, length, diameter = pipe_split[:5]

        elevation_a, elevation_b = self.get_elevation(node_a), self.get_elevation(node_b)
        if elevation_a > elevation_b:
            node_a, node_b = node_b, node_a
            elevation_a, elevation_b = elevation_b, elevation_a

        d_z, elevation_min = elevation_b - elevation_a, elevation_a

        # if height difference is 0 need to intervene so we don't get a tank with 0 height
        d_z = 1 if d_z == 0 else d_z

        volume = 3.141 / 4 * (float(diameter) ** 2) * float(length)
        diameter_equivalent = np.sqrt(4 * volume / np.pi / d_z)
        return pipe_id, node_a, node_b, float(length), diameter, d_z, elevation_min, volume, diameter_equivalent

    def create_intermittent_network(self) -> str:
        # all pipes in the network must be initially closed
        self.set_initial_pipes_closed()
        initial_pipes = self.content["PIPES"].copy()

        for pipe in initial_pipes:
            # skip over comments
            if self.is_comment(pipe):
                continue

            pipe_id, node_a, node_b, length, diameter, d_z, elevation, volume, diameter_equivalent = self.parse_pipe(
                pipe)

            tank_id = self.add_tank(f"{node_a}_{node_b}_tank", elevation, d_z, diameter_equivalent)

            # TODO: create a class that handles connecting the tank to the nodes so that I can try
            # TODO: different strategies

            # lower node; pipe sloping up (need check valve to prevent backflow)
            equivalent_pipe = self.converter.equivalent_length(length, d_z)
            self.add_pipe(node_a, tank_id, equivalent_pipe, diameter, "CV")

            # upper node; pipe sloping down (need PSV)
            equivalent_pipe = self.converter.equivalent_length(length, -d_z)
            print(f"pipe sloping down equivalent length: {equivalent_pipe}, length: {length}, d_z: {d_z}")
            psv_start, psv_end = self.add_psv(node_b, node_a)
            self.add_pipe(node_b, psv_start, equivalent_pipe, diameter)  # original node to PSV
            self.add_pipe(psv_end, tank_id, 1, 1000)  # PSV to tank

            self.content["PIPES"].append(";")
            # TODO: tank level is elevation + d_z or just d_z?
            self.add_rule(tank_id, elevation + d_z, pipe_id)
        pass


if __name__ == "__main__":
    test_file_path = 'test_files/pipe.inp'
    # bad dependency injection lol
    converter = PipeConverter(20, 1)
    parser = FileParser(test_file_path, converter)
    parser.create_intermittent_network()
    reconstructed = parser.reconstruct_file()
    print(reconstructed)
