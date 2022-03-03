import wntr
from PipeConverter import PipeConverter
from FileParser import FileParser
import argparse
import os


class WNTRWrapper:
    def __init__(self, file: str, is_iwn: bool = False) -> None:
        self.file = file
        self.is_iwn = is_iwn
        if is_iwn:
            self.file_iwn = self.create_modified_network()
            self.wn = wntr.network.WaterNetworkModel(self.file_iwn)
        else:
            self.wn = wntr.network.WaterNetworkModel(self.file)

    def create_modified_network(self) -> str:
        # TODO: ideally these are passed as options to the class
        converter = PipeConverter()
        parser = FileParser(self.file, converter)

        parser.create_intermittent_network()
        reconstructed = parser.reconstruct_file()

        file_iwn = self.file.split(".inp")[0] + "_iwn.inp"
        with open(file_iwn, 'w') as f:
            f.write(reconstructed)

        return file_iwn

    def run_sim(self, file_prefix: str = os.path.join("reports", "test")):
        sim = wntr.sim.EpanetSimulator(self.wn)
        sim.run_sim(file_prefix=file_prefix)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", help="filepath", type=str)
    parser.add_argument("--create_iwn", help="pipe diameter", type=bool, default=False)
    args = parser.parse_args()

    wrapper = WNTRWrapper(args.filepath, args.create_iwn)
    wrapper.run_sim()
