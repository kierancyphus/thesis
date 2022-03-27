from enum import Enum
from ParsedPipe import ParsedPipe
import numpy as np


class Strategy(Enum):
    MULTIPLE_TANKS = 1
    SINGLE_TANK_CV = 2  # the pressure is assumed to be 2x change in height
    SINGLE_TANK_PSV = 3
    SINGLE_TANK_CV_CONSTANT_PRESSURE = 4  # pressure is assumed to be constant


class ModificationStrategy:
    def __init__(self, file_parser, strategy: Strategy = Strategy.SINGLE_TANK_CV, tank_height_multiplier: float = 1,
                 cf: float = 1):
        self.strategy = strategy
        self.file_parser = file_parser
        self.methods = {
            Strategy.MULTIPLE_TANKS: self.multiple_tanks,
            Strategy.SINGLE_TANK_CV: self.single_tank_cv,
            Strategy.SINGLE_TANK_PSV: self.single_tank_psv,
            Strategy.SINGLE_TANK_CV_CONSTANT_PRESSURE: self.single_tank_cv_constant_pressure
        }
        self.tank_height_multiplier = tank_height_multiplier
        self.cf = cf

    def evaluate(self, pipe: ParsedPipe) -> None:
        self.methods[self.strategy](pipe)
        return

    def multiple_tanks(self, pipe: ParsedPipe) -> None:
        raise NotImplementedError()

    def update_tank_height_diameter(self, pipe: ParsedPipe) -> None:
        volume = 3.141 / 4 * (float(pipe.diameter) ** 2) * float(pipe.length)
        # the tank height is scaled by a global factor. This is used to test the effect of tank height on resistance
        tank_d_z = pipe.d_z * self.tank_height_multiplier if pipe.d_z > 0.1 else 0.1
        tank_diameter = np.sqrt(4 * volume / np.pi / tank_d_z)
        # print(f"height: {tank_d_z}, diameter: {tank_diameter}")
        pipe.update_tank_info(tank_diameter, tank_d_z)
        return

    def single_tank_cv(self, pipe: ParsedPipe, update_pressure=True) -> None:
        # calculate tank equivalent parameters
        self.update_tank_height_diameter(pipe)

        # insert a new tank with volume the same as that of the original pipe
        tank_id = self.file_parser.add_tank(f"{pipe.node_a}_{pipe.node_b}_tank", pipe.elevation_min, pipe.tank_height,
                                            pipe.tank_diameter)

        # lower node; pipe sloping up (need check valve to prevent backflow)
        equivalent_pipe = self.file_parser.converter.equivalent_length(pipe.length, pipe.d_z, pipe.diameter,
                                                                       update_pressure=update_pressure)
        # print(f"up slope, d_z = {pipe.d_z}, leq = {equivalent_pipe}")
        self.file_parser.add_pipe(pipe.node_a, tank_id, equivalent_pipe, pipe.diameter, "CV")

        # upper node; pipe sloping down (need check valve to prevent backflow)
        equivalent_pipe = self.file_parser.converter.equivalent_length(pipe.length, -pipe.d_z, pipe.diameter,
                                                                       update_pressure=update_pressure,
                                                                       cf=self.cf)
        # print(f"down slope, d_z = {-pipe.d_z}, leq = {equivalent_pipe}")
        self.file_parser.add_pipe(pipe.node_b, tank_id, equivalent_pipe, pipe.diameter, "CV")

        # update the rules
        self.file_parser.add_rule(tank_id, pipe.tank_height, pipe.pipe_id)
        return

    def single_tank_cv_constant_pressure(self, pipe: ParsedPipe) -> None:
        self.single_tank_cv(pipe, update_pressure=False)
        return

    def single_tank_psv(self, pipe: ParsedPipe) -> None:
        raise NotImplementedError()
        # TODO: I think this is broken
        tank_id = self.file_parser.add_tank(f"{pipe.node_a}_{pipe.node_b}_tank", pipe.elevation_min, pipe.d_z,
                                            pipe.tank_diameter)

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
