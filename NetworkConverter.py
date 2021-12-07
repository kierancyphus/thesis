import wntr
from wntr.network.base import LinkStatus
from wntr.network.elements import Tank
from typing import List, Tuple

# TODO: Need to abstract this to a strategy class
class SameLength:
    def get_equivalent_length(self, length: float) -> float:
        return length


class NetworkConverter:
    def __init__(self, filepath: str) -> None:
        """
        :param filepath: path to inp file to be changed
        """

        self.filepath: str = filepath
        self.wn = wntr.network.WaterNetworkModel(filepath)
        self.pipe_converter = None

    def _close_all_pipes(self) -> None:
        """
        Sets the Status of all Pipes to Closed
        :return:
        """
        for _, pipe in self.wn.pipes():
            pipe._initial_status = LinkStatus.Closed
            pipe._internal_status = LinkStatus.Closed
            pipe._user_status = LinkStatus.Closed

    def _get_pipe_equivalent_lengths(self) -> Tuple[str, str, float, float]:
        """

        :return: (name, start_node, length, diameter)
        """
        self.wn.get_graph()
        pipe_info = []
        for name, pipe in self.wn.pipes():
            # TODO: extract to function get_shadow_name (in case I want to change it)
            new_name = name + "_shadow"
            new_start_node = pipe.start_node_name
            diameter = pipe._diameter

            length = self.pipe_converter()



    def _create_tanks(self) -> List[Tank]:
        """

        :return: a List of tanks with volumes in
        """


    def convert_network(self, strategy: str = "") -> None:
        """

        :param strategy: this will be an enum saying how we should handle equivalent pipe lengths, e.g. constant slope,
                            constant height...
        :return: Nothing, it modifies the existing graph structure
        """
        # choose converter
        # TODO: Implement switcher here
        self.pipe_converter = SameLength()

        # set all pipes to closed
        self._close_all_pipes()

        # calculate equivalent pipe lengths


        # create tanks and connect all pipes


        # add rules to open original pipes



if __name__ == "__main__":
    filepath = "test_files/test.inp"
    converter = NetworkConverter(filepath)
    print(converter.wn)

