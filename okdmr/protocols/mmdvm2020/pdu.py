def _mmdvm2020_repeater_id_field(
        repeater_id: int
) -> bytes:
    """
    Convert RepeaterID to bytes as expected in MMDVM2020 protocol
    :param repeater_id:
    :return:
    """
    assert repeater_id > 0, "RepeaterID must be positive number"
    return repeater_id.to_bytes(4, byteorder='big')


def mmdvm2020_ack_with_challenge(
        repeater_id: int,
        challenge: bytes
) -> bytes:
    """
    Generate RPTACK with login challenge
    :param repeater_id:
    :param challenge: 4 bytes
    :return:
    """
    assert len(challenge) == 4, "Challenge must be 4 bytes long"
    return mmdvm2020_ack(repeater_id) + challenge


def mmdvm2020_ack(
        repeater_id: int
) -> bytes:
    """
    Generate
    :param repeater_id:
    :return:
    """
    return (
            "RPTACK".encode('ASCII')
            + _mmdvm2020_repeater_id_field(repeater_id)
    )


def mmdvm2020_pong(
        repeater_id: int
) -> bytes:
    return (
            "MSTPONG".encode('ASCII')
            + _mmdvm2020_repeater_id_field(repeater_id)
    )


def mmdvm2020_negative_ack(
        repeater_id: int
) -> bytes:
    return (
            "MSTNAK".encode('ASCII')
            + _mmdvm2020_repeater_id_field(repeater_id)
    )
