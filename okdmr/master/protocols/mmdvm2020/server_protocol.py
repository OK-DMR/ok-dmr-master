import random
import string
import traceback
from asyncio import protocols, transports
from typing import Optional, Tuple, Dict

from okdmr.dmrlib.etsi.layer2.burst import Burst
from okdmr.kaitai.homebrew.mmdvm2020 import Mmdvm2020

from okdmr.master.utils import prettyprint
from okdmr.master.protocols.mmdvm2020.peer import MMDVM2020Peer
from okdmr.dmrlib.transmission.transmission_watcher import TransmissionWatcher


class Mmdvm2020ServerProtocol(protocols.DatagramProtocol):
    def __init__(self):
        self.peers: Dict[int, MMDVM2020Peer] = {}
        self.transport: Optional[transports.DatagramTransport] = None
        self.watcher: TransmissionWatcher = TransmissionWatcher()

    def get_peer(
        self,
        repeater_id: int,
        address: Tuple[str, int],
        create_if_not_exists: bool = False,
    ) -> Optional[MMDVM2020Peer]:
        peer: Optional[MMDVM2020Peer] = self.peers.get(repeater_id)
        if peer:
            return peer if peer.check_origin(address=address) else None
        return (
            self.create_peer(address=address, repeater_id=repeater_id)
            if create_if_not_exists
            else None
        )

    def create_peer(self, address: Tuple[str, int], repeater_id: int):
        if self.peers.get(repeater_id):
            raise Exception(f"Peer {repeater_id} already exists")
        self.peers[repeater_id] = MMDVM2020Peer(
            address=address, repeater_id=repeater_id
        )
        return self.peers[repeater_id]

    @staticmethod
    def get_repeater_id(packet: Mmdvm2020) -> int:
        if hasattr(packet.command_data, "repeater_id"):
            return packet.command_data.repeater_id
        elif hasattr(packet.command_data, "repeater_id_or_challenge"):
            return packet.command_data.repeater_id_or_challenge
        elif hasattr(packet.command_data, "data") and hasattr(
            packet.command_data.data, "repeater_id"
        ):
            return packet.command_data.data.repeater_id
        prettyprint(packet)
        raise Exception("packet no repeater_id")

    @staticmethod
    def parse_mmdvm2020_data(packet: bytes) -> Optional[Tuple[Mmdvm2020, int]]:
        # noinspection PyBroadException
        try:
            received: Mmdvm2020 = Mmdvm2020.from_bytes(packet)
            repeater_id: int = Mmdvm2020ServerProtocol.get_repeater_id(received)
            return received, repeater_id
        except:
            print(f"Invalid Mmdvm2020 packet received {packet.hex()}")
            traceback.print_exc()
        return None

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        dgram_id: str = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=8)
        )
        parse: Optional[Tuple[Mmdvm2020, int]] = self.parse_mmdvm2020_data(data)
        if not parse:
            return
        received, repeater_id = parse

        # Check peer information
        peer: Optional[MMDVM2020Peer] = self.get_peer(
            repeater_id=repeater_id, address=addr, create_if_not_exists=True
        )
        if not peer:
            print(f"{dgram_id} Could not get peer {repeater_id} for {addr}")
            return

        response: Optional[bytes] = peer.process_datagram(
            datagram=received, log_tag=dgram_id + " "
        )
        if isinstance(received.command_data, Mmdvm2020.TypeDmrData):
            self.watcher.process_burst(Burst.from_mmdvm(mmdvm=received.command_data))
        if response:
            check: Optional[Tuple[Mmdvm2020, int]] = self.parse_mmdvm2020_data(response)
            if check:
                self.transport.sendto(data=response, addr=addr)
                print(
                    f"{dgram_id} Response sent {check[0].command_data.__class__.__name__}"
                )
            else:
                print(
                    f"{dgram_id} Response is not valid Mmdvm2020 packet {response.hex()}"
                )
        else:
            print(f"{dgram_id} No response sent to repeater")

    def connection_made(self, transport: transports.BaseTransport) -> None:
        self.transport = transport

    def error_received(self, exc: Exception) -> None:
        print("error_received", exc)
