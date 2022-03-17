from typing import Optional


class ParsedPipe:
    """
    DTO for pipes -> including their equivalent counterparts
    """
    def __init__(self, pipe_id: str, node_a: str, node_b: str, length: float, diameter: float, d_z: float,
                 elevation_min: float, tank_diameter: Optional[float] = None, tank_height: Optional[float] = None):
        self.pipe_id = pipe_id
        self.node_a = node_a
        self.node_b = node_b
        self.length = length
        self.diameter = diameter
        self.d_z = d_z
        self.elevation_min = elevation_min
        self.tank_diameter = tank_diameter
        self.tank_height = tank_height

    def update_tank_info(self, tank_diameter: float, tank_height: float) -> None:
        self.tank_height = tank_height
        self.tank_diameter = tank_diameter
