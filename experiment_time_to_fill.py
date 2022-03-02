from PipeConverter import PipeConverter
import argparse
from typing import Union

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--length", help="pipe length [m]", type=float)
    parser.add_argument("-d", "--diameter", help="pipe diameter [m]", type=float)
    parser.add_argument("-e", "--elevation", help="change in height [m]", type=float)
    args = parser.parse_args()

    converter = PipeConverter()
    # consider the flat pipe case
    pressure = args.elevation * 2 if args.elevation != 0 else 20
    converter.update_pressure(pressure)
    equivalent = converter.equivalent_length(args.length, args.elevation, args.diameter)
    print(f"Equivalent length: {equivalent}")

