from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np


class IPipe(ABC):
    def __init__(self, delta_h: float, c: float, theta: float, length: float) -> None:
        self.delta_h = delta_h
        self.c = c
        self.theta = theta
        self.length = length
        self.delta_z = length * np.sin(theta)

    @abstractmethod
    def fill_numerically(self, t: np.ndarray, plot=False) -> Tuple[np.ndarray, np.ndarray]:
        pass

    @abstractmethod
    def get_equivalent_length(self) -> float:
        pass
