from Pipe import Pipe, Experimenter
import numpy as np

if __name__ == "__main__":
    # test a really small incline, the ratio should roughly be 0.44
    pipe = Pipe(1000, 1, 0, 10)
    # time = np.linspace(0, 20, 500)
    # pipe.plot_flat_vs_angled(time)
    pipe.numerically_calculate_equivalent_length()

    experimenter = Experimenter(np.linspace(10, 3000, 100), np.linspace(-np.pi/8, np.pi/8, 100), np.linspace(1, 10, 20))
    experimenter.run_numerical_experiments(constant_slope=True)
