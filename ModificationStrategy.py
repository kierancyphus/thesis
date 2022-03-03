from enum import Enum
from ParsedPipe import ParsedPipe


class Strategy(Enum):
    MULTIPLE_TANKS = 1
    SINGLE_TANK_CV = 2
    SINGLE_TANK_PSV = 3


class ModificationStrategy:
    def __init__(self, file_parser, strategy: Strategy = Strategy.SINGLE_TANK_CV) -> None:
        self.strategy = strategy
        self.file_parser = file_parser
        self.methods = {
            Strategy.MULTIPLE_TANKS: self.multiple_tanks,
            Strategy.SINGLE_TANK_CV: self.single_tank_cv,
            Strategy.SINGLE_TANK_PSV: self.single_tank_psv
        }

    def evaluate(self, pipe: ParsedPipe) -> None:
        self.methods[self.strategy](pipe)
        return

    def multiple_tanks(self, pipe: ParsedPipe) -> None:
        raise NotImplementedError()

    def single_tank_cv(self, pipe: ParsedPipe) -> None:
        update_pressure = False

        # insert a new tank with volume the same as that of the original pipe
        # print(pipe.diameter_equivalent)
        tank_id = self.file_parser.add_tank(f"{pipe.node_a}_{pipe.node_b}_tank", pipe.elevation_min, pipe.d_z,
                                            pipe.diameter_equivalent)

        # lower node; pipe sloping up (need check valve to prevent backflow)
        equivalent_pipe = self.file_parser.converter.equivalent_length(pipe.length, -pipe.d_z, pipe.diameter, update_pressure=update_pressure)
        self.file_parser.add_pipe(pipe.node_a, tank_id, equivalent_pipe, pipe.diameter, "CV")

        # upper node; pipe sloping down (need check valve to prevent backflow)
        equivalent_pipe = self.file_parser.converter.equivalent_length(pipe.length, pipe.d_z, pipe.diameter, update_pressure=update_pressure)
        self.file_parser.add_pipe(pipe.node_b, tank_id, equivalent_pipe, pipe.diameter, "CV")

        # update the rules
        # if the pipe is flat, the tank is assumed to have a height of 1m
        tank_level = 1 if pipe.d_z == 0 else pipe.d_z
        self.file_parser.add_rule(tank_id, tank_level, pipe.pipe_id)
        return

    def single_tank_psv(self, pipe: ParsedPipe) -> None:
        raise NotImplementedError()
        # TODO: I think this is broken
        tank_id = self.file_parser.add_tank(f"{pipe.node_a}_{pipe.node_b}_tank", pipe.elevation_min, pipe.d_z, pipe.diameter_equivalent)

        # lower node; pipe sloping up (need check valve to prevent backflow)
        equivalent_pipe = self.file_parser.converter.equivalent_length(pipe.length, -pipe.d_z, pipe.diameter)
        self.file_parser.add_pipe(pipe.node_a, tank_id, equivalent_pipe, pipe.diameter, "CV")

        # upper node; pipe sloping down (need PSV)
        equivalent_pipe = self.file_parser.converter.equivalent_length(pipe.length, pipe.d_z, pipe.diameter)
        print(f"pipe sloping down equivalent length: {equivalent_pipe}, length: {pipe.length}, d_z: {pipe.d_z}")
        psv_start, psv_end = self.file_parser.add_psv(pipe.node_b, pipe.node_a)
        self.file_parser.add_pipe(pipe.node_b, psv_start, equivalent_pipe, pipe.diameter)  # original node to PSV
        self.file_parser.add_pipe(psv_end, tank_id, 1, 1000)  # PSV to tank

        self.file_parser.content["PIPES"].append(";")
        self.file_parser.add_rule(tank_id, pipe.d_z, pipe.pipe_id)
        pass
