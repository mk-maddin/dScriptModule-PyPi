"""Shared fixtures: an emulated dScript board running the custom firmware protocol."""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

STATUS = bytes([34, 4, 13, 3, 8, 120, 1, 11])          # dS2824, FW 4.13, App 3.8, 12.0V, 26.7C
CONFIG = bytes([0, 1, 2, 0xab, 4, 5, 24, 4, 3, 12, 1, 2])  # MAC, 24 relays, 4 lights, 3 shutters, 12 sockets, 1 motion, 2 buttons


class FakeBoard:
    """Minimal asyncio TCP server answering like the dScriptRoomControl firmware (one request per connection)."""

    def __init__(self, fragment=False, silent=False, delay=0.02):
        self.fragment = fragment
        self.silent = silent
        self.delay = delay
        self.requests = []
        self.active = 0
        self.max_active = 0
        self.server = None
        self.port = None

    def response(self, cmd, arg):
        if cmd == 0x30: return STATUS
        if cmd == 0x50: return CONFIG
        if cmd == 0x51: return bytes([1 if arg == 1 else 0])     # light 1 on, others off
        if cmd == 0x52: return bytes([55, 0])                     # shutter at 55%, stopped
        if cmd == 0x53: return bytes([1])                         # socket on
        if cmd == 0x54: return bytes([0])                         # no motion
        if cmd == 0x55: return bytes([3])                         # 3 clicks
        if cmd in (0x31, 0x40, 0x41, 0x42): return bytes([0])     # ACK
        return bytes([0xff])

    async def handle(self, reader, writer):
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            data = await reader.read(100)
            self.requests.append(bytes(data))
            if self.silent:
                await asyncio.sleep(30)
                return
            await asyncio.sleep(self.delay)
            resp = self.response(data[0], data[1] if len(data) > 1 else 0)
            if self.fragment and len(resp) > 1:
                writer.write(resp[:1]); await writer.drain(); await asyncio.sleep(0.02)
                writer.write(resp[1:])
            else:
                writer.write(resp)
            await writer.drain()
        finally:
            self.active -= 1
            writer.close()

    async def start(self):
        self.server = await asyncio.start_server(self.handle, '127.0.0.1', 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def stop(self):
        self.server.close()
        await self.server.wait_closed()


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, timeout=60))


@pytest.fixture
def fake_board_cls():
    return FakeBoard
