def mmdvm2020_ack_with_challenge(
        repeater_id: int,
        challenge: bytes
) -> bytes:
    return mmdvm2020_ack(repeater_id) + challenge[:4]


def mmdvm2020_ack(
        repeater_id: int
) -> bytes:
    return (
            "RPTACK".encode('ASCII')
            + repeater_id.to_bytes(4, byteorder='big')
    )


def mmdvm2020_pong(
        repeater_id: int
) -> bytes:
    return (
            "MSTPONG".encode('ASCII')
            + repeater_id.to_bytes(4, byteorder='big')
    )
