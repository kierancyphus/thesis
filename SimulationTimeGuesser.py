from typing import Union


class SimulationTimeGuesser:
    def __init__(self, length: int, height: int, offset: int = 600, type: str = "linear_length"):
        self.length = length
        self.height = height
        # default offset is 10 minutes
        self.offset = offset
        self.type = type

    def evaluate(self) -> Union[int, float]:
        return getattr(self, self.type)()

    def linear_length(self) -> Union[int, float]:
        return self.length

    def linear_length_offset(self) -> Union[int, float]:
        return self.length + self.offset

    def poly_length_offset(self) -> Union[int, float]:
        return self.length ** 1.45 + self.offset

    def quadratic_length(self) -> Union[int, float]:
        return self.length ** 2

    def quadratic_length_offset(self) -> Union[int, float]:
        return self.length ** 2 + self.offset
