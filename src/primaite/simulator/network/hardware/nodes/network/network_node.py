from primaite.simulator.network.hardware.base import Node, NetworkInterface
from primaite.simulator.network.transmission.data_link_layer import Frame


class NetworkNode(Node):
    """"""

    def receive_frame(self, frame: Frame, from_network_interface: NetworkInterface):
        pass
