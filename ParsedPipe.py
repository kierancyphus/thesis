class ParsedPipe:
    def __init__(self, pipe_id: str, node_a: str, node_b: str, length: float, diameter: float, d_z: float,
                 elevation_min: float, volume: float, diameter_equivalent: float):
        self.pipe_id = pipe_id
        self.node_a = node_a
        self.node_b = node_b
        self.length = length
        self.diameter = diameter
        self.d_z = d_z
        self.elevation_min = elevation_min
        self.volume = volume
        self.diameter_equivalent = diameter_equivalent
