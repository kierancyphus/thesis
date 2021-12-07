from typing import List, Dict, Union


class FileParser:
    def __init__(self, file_path: str) -> None:
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

    def valid_input(self):
        return "TANKS" in self.headers and "PIPES" in self.headers and "RULES" in self.headers

    def get_headers(self) -> List[str]:
        headers = []
        for line in self.file:
            if len(line) > 0:
                if line[0] == "[" and line[-1] == "]":
                    headers.append(line[1: -1])
        return headers

    def get_content(self) -> Dict[str, List[str]]:
        # returns a dict mapping section to content lines
        content_dict = {}
        accum = []
        current = ""
        for line in self.file:
            # skip first case
            if len(line) > 0:
                # if this is a header (eliminates whitespace)
                if line.strip()[1: -1] in self.headers:
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

    def add_rule(self, tank_id: str, tank_level, pipe_id: str) -> str:
        # TODO: check if I'm actually supposed to use tabs
        if not self.added_rule:
            self.added_rule = True
            self.content["RULES"].append(self.comment)
        rule = f"RULE\t{self.rule_count}\nIF\tTANK\t{tank_id}\tLEVEL\tABOVE\t{tank_level}\nTHEN\tPIPE\t{pipe_id}\tSTATUS\tIS\tOPEN\n\n "
        self.rule_count += 1
        self.content["RULES"].append(rule)
        return rule

    def add_tank(self, id: str, elevation: int, init_level: int, min_level: int, max_level: int,
                 diameter: Union[float, int], min_vol: int) -> str:
        if not self.added_tank:
            self.added_tank = True
            self.content["TANKS"].append(self.comment)
        tank = "\t".join([id, elevation, init_level, min_level, max_level, diameter, min_vol, "", "\t"])
        self.content["TANKS"].append(tank)
        return tank

    def add_pipe(self, node_a: Union[str, int], node_b: Union[str, int], length: Union[str, int],
                 diameter: Union[str, int]) -> str:
        """
        Used for adding shadow pipes - the id will always be f"{id[node_a]}__{id[node_b]}".
        It might visually look a bit different, but when you upload the model it strips whitespace, so the tabs are important here

        Roughness and Minor loss are both set to be 0
        :param node_a:
        :param node_b:
        :param length:
        :param diameter:
        :return:
        """
        if not self.added_pipe:
            self.added_pipe = True
            self.content["PIPES"].append(self.comment)
        pipe = f" {node_a}__{node_b}\t{node_a}\t{node_b}\t{length}\t{diameter}\t100\t0\tOpen\t;"
        self.content["PIPES"].append(pipe)
        return pipe

    def create_intermittent_network(self) -> str:
        for pipe in self.content["PIPES"]:
            # self.set_initial_pipes_closed()
            pass
            # info = self.parse_pipe(pipe)
            # sloping downwards
            # equivalent_pipe = self.converter.convert_pipe(info, 'downwards')
            # self.add_tank(...)
            # self.add_pipe(...)
            # self.add_rule(...)
            # sloping upwards
            # equivalent_pipe = self.converter.convert_pipe(info, 'upwards')
            # self.add_tank(...)
            # self.add_pipe(...)
            # self.add_rule(...)
        pass


if __name__ == "__main__":
    test_file_path = 'test_files/test.inp'
    parser = FileParser(test_file_path)
    # print(parser.headers)
    parser.add_pipe(10, 2, 10000, 18)
    for key, item in parser.content.items():
        if key == "PIPES":
            for line in item:
                print(line)
    parser.add_rule("2", "100", "2")
    reconstructed = parser.reconstruct_file()
    # print(reconstructed)
    # print(parser.rule_count)
