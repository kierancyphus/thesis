from PipeConverter import PipeConverter
import argparse
from typing import Union
import matplotlib.pyplot as plt

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
    tau, t, x = converter.fill_time(args.length, args.elevation, args.diameter, update_pressure=False, return_fronts=True)
    print(f"Fill time: {tau} s")
    print(f"{int(tau // 60)}:{tau % 60:.0f}")
    equivalent = converter.equivalent_length(args.length, args.elevation, args.diameter, update_pressure=False)
    print(f"Equivalent length: {equivalent}")

    plt.plot(t[:len(t) // 2], x[:len(x) // 2])
    plt.scatter([318, 918, 1722, 2688], [1000, 2000, 3000, 4000], c='r', alpha=0.5)
    plt.legend(['Mathematical filling front', 'EPANET filling front'])
    plt.xlabel('Time [s]')
    plt.ylabel('Location of filling front [m]')
    plt.title('Location of filling front [m] vs Time [s]')
    plt.show()

    # derivative
    v = [0] + [x[i] - x[i - 1] for i in range(1, len(x))]
    plt.plot(t, v)
    plt.show()
