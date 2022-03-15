import os
import pickle as pkl


class FrictionFactorCalculator:
    def __init__(self, length: float, diameter: float, pressure: float, roughness: float = 100):
        self.length = length
        self.diameter = diameter
        self.pressure = pressure
        self.roughness = roughness

        # calculate dictionary indeces
        self.length_closest = self.get_nearest_length()
        self.diameter_closest = self.get_nearest_diameter()
        self.pressure_closest = self.get_nearest_pressure()

        self.lookup_table_path = os.path.join(os.getcwd(), 'lookup_table.pkl')
        self.lookup_table = self.get_lookup_table()

    def get_lookup_table(self):
        return {}
        if not os.path.exists('lookup_table_path'):
            raise ValueError(f"No lookup table at {self.lookup_table_path}. Could not calculate friction factors")

        with open(self.lookup_table_path, 'r') as f:
            lookup_table = pkl.load(f)

        return lookup_table

    def get_nearest_length(self) -> int:
        # buckets are every 100m and are indexed by the min
        if self.length < 100:
            raise ValueError("Currently don't support pipes less than 100m long")

        return int((self.length // 100) * 100)

    def get_nearest_diameter(self) -> float:
        if self.diameter == 0.3:
            return 0.3
        raise NotImplementedError("Currently only support pipe lengths of 0.3m. More experiments required to calculate others")

    def get_nearest_pressure(self) -> int:
        return 20
        if self.pressure == 20:
            return 20
        raise NotImplementedError("Currently only support pressure head of 20m. More experiments required to calculate others")

    def get_friction_factor(self) -> float:
        # 0.0263 for pressure 40
        # 0.0282 for pressure 20
        return 0.0275
        return self.lookup_table[self.length_closest][self.diameter_closest][self.pressure_closest]
