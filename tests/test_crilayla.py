import random

import pytest

from tools import cpk, crilayla

noise = random.Random(1).randbytes


@pytest.mark.parametrize("data", [
    b"x" * 1000,                                # one long run: length levels past 0xFF
    noise(700),                            # incompressible: literals only
    bytes(range(256)) * 40,                     # repeats at the 256-byte distance
    b"ab" * 3000 + noise(50),              # overlapping copies (distance < length)
    noise(300) + bytes(9000) + noise(300),  # match longer than MAX_DIST
], ids=["run", "literals", "period256", "overlap", "long"])
def test_compress_round_trips_through_both_decoders(data):
    c = crilayla.compress(data)
    assert c[:8] == b"CRILAYLA"
    assert (len(c) - 0x10 - 0x100) % 4 == 0      # bitstream padded to 4 bytes like the game's files
    assert cpk.decompress_crilayla(c) == data
    assert crilayla.decompress(c) == data


def test_compress_rejects_data_without_a_body():
    with pytest.raises(ValueError):
        crilayla.compress(bytes(0x100))
