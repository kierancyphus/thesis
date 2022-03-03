from PipeConverter import PipeConverter
import argparse
from typing import Union

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--length", help="pipe length [m]", type=float)
    parser.add_argument("-d", "--diameter", help="pipe diameter [m]", type=float)
    parser.add_argument("-e", "--elevation", help="change in height [m]", type=float)
    parser.add_argument("-p", "--pressure", help="pressure head [m]", type=float)
    args = parser.parse_args()

    converter = PipeConverter()
    # consider the flat pipe case
    pressure = args.elevation * 2 if args.pressure is None else args.pressure
    converter.update_pressure(pressure)
    time = converter.fill_time(args.length, args.elevation, args.diameter, update_pressure=False)
    print(f"Fill time: {time} s")
    print(f"{int(time // 60)}:{time % 60:.0f}")
    equivalent = converter.equivalent_length(args.length, args.elevation, args.diameter, update_pressure=False)
    print(f"Equivalent length: {equivalent}")

