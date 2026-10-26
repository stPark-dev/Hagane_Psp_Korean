import json

from tools import ppdbg


def test_client_frame_is_masked_text_and_roundtrips():
    payload = json.dumps({"event": "game.status"}).encode()
    frame = ppdbg.encode_frame(payload, mask_key=b"\x01\x02\x03\x04")
    assert frame[0] == 0x81            # FIN + text
    assert frame[1] & 0x80             # masked (client -> server)
    opcode, data, consumed = ppdbg.decode_frame(frame)
    assert (opcode, data, consumed) == (1, payload, len(frame))


def test_extended_lengths():
    for n in (125, 126, 70000):
        payload = b"x" * n
        frame = ppdbg.encode_frame(payload, mask_key=b"\0\0\0\0")
        opcode, data, consumed = ppdbg.decode_frame(frame)
        assert data == payload and consumed == len(frame)


def test_decode_incomplete_frame_returns_none():
    frame = ppdbg.encode_frame(b"hello", mask_key=b"abcd")
    assert ppdbg.decode_frame(frame[:-1]) is None


def test_unmasked_server_frame():
    frame = bytes([0x81, 5]) + b"hello"
    assert ppdbg.decode_frame(frame) == (1, b"hello", 7)
