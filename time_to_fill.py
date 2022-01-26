from PipeConverter import PipeConverter
import argparse
from typing import Union

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--length", help="pipe length", type=float)
    parser.add_argument("--diameter", help="pipe diameter", type=float)
    parser.add_argument("--elevation", help="change in height", type=float)
    args = parser.parse_args()

    converter = PipeConverter()
    converter.update_pressure(args.elevation * 2)
    equivalent = converter.equivalent_length(args.length, args.elevation, args.diameter)

