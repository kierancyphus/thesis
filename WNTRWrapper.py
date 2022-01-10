# import wntr
from PipeConverter import PipeConverter
from FileParser import FileParser


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

    def run_sim(self):
        sim = wntr.sim.EpanetSimulator(self.wn)
        results = sim.run_sim()
        print(results)


if __name__ == "__main__":
    wrapper = WNTRWrapper("./test_files/pipe.inp", True)
    wrapper.run_sim()
