import secrets
from typing import Tuple, Optional

from okdmr.kaitai.homebrew.mmdvm2020 import Mmdvm2020

from okdmr.master.utils import prettyprint
from okdmr.protocols.mmdvm2020.pdu import mmdvm2020_ack_with_challenge, mmdvm2020_ack, mmdvm2020_pong, \
    mmdvm2020_negative_ack


class MMDVM2020Peer:
    STATE_NEW: int = -1
    STATE_CLOSED: int = 0
    STATE_AUTHORIZED: int = 1
    STATE_EXPIRED: int = 5

    def __init__(self, address: Tuple[str, int], repeater_id: int):
        """
        Peer is identified by repeater_id and address it is connected from
        :param address:
        :param repeater_id:
        """
        self.address: Tuple[str, int] = address
        self.repeater_id: int = repeater_id
        self.last_configuration: Optional[Mmdvm2020.TypeRepeaterConfiguration] = None
        self.state: int = self.STATE_NEW
        self.login_challenge: bytes = secrets.token_bytes(4)

    def check_origin(self, address: Tuple[str, int], throw: bool = False):
        """
        Remote IP address must match, sending port not as it might change over time
        :param address: [ip, port]
        :param throw: whether to raise exception if check does not pass
        :return: check result
        """
        if self.address[0] == address[0]:
            return True
        if throw:
            raise Exception(f"Peer {self.repeater_id} address {self.address} does not match {address}")
        return False

    def process_login_request(self, request: Mmdvm2020.TypeRepeaterLoginRequest) -> Optional[bytes]:
        if self.state == self.STATE_AUTHORIZED:
            print(f"Ignore duplicate login request from {self.repeater_id}")
            return
        return mmdvm2020_ack_with_challenge(repeater_id=self.repeater_id, challenge=self.login_challenge)

    def process_login_response(self, response: Mmdvm2020.TypeRepeaterLoginResponse) -> Optional[bytes]:
        self.state = self.STATE_AUTHORIZED
        return mmdvm2020_ack(repeater_id=self.repeater_id)

    def process_repeater_configuration(self, config: Mmdvm2020.TypeRepeaterConfiguration) -> Optional[bytes]:
        self.last_configuration = config
        return mmdvm2020_ack(config.repeater_id)

    def process_repeater_closing(self, message: Mmdvm2020.TypeRepeaterClosing):
        self.state = self.STATE_CLOSED

    def process_repeater_ping(self, message: Mmdvm2020.TypeRepeaterPing):
        return (
            mmdvm2020_pong(repeater_id=self.repeater_id)
            if self.state == self.STATE_AUTHORIZED else
            mmdvm2020_negative_ack(repeater_id=self.repeater_id)
        )

    def process_datagram(self, datagram: Mmdvm2020, log_tag: str = "") -> Optional[bytes]:
        command_data = datagram.command_data
        print(f"{log_tag}Peer {self.repeater_id} sent {command_data.__class__.__name__} from {self.address}")

        if isinstance(command_data, Mmdvm2020.TypeRepeaterLoginRequest):
            return self.process_login_request(command_data)
        elif isinstance(command_data, Mmdvm2020.TypeRepeaterLoginResponse):
            return self.process_login_response(command_data)
        elif isinstance(command_data, Mmdvm2020.TypeRepeaterConfigurationOrClosing):
            if isinstance(command_data.data, Mmdvm2020.TypeRepeaterConfiguration):
                return self.process_repeater_configuration(command_data.data)
            elif isinstance(command_data.data, Mmdvm2020.TypeRepeaterClosing):
                return self.process_repeater_closing(command_data.data)
        elif isinstance(command_data, Mmdvm2020.TypeRepeaterPing):
            return self.process_repeater_ping(command_data)
        else:
            print(f"{log_tag}Peer {self.repeater_id} unhandled {command_data.__class__.__name__}")
            prettyprint(command_data, log_tag=log_tag)
