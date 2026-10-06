"""Tests for dScriptBoard communication."""
import asyncio
import time

from conftest import run
from dScriptModule import dScriptBoard


def make_board(port, timeout=2):
    board = dScriptBoard('127.0.0.1', port)
    board.ConnectionTimeout = timeout
    return board


def test_async_status_and_config(fake_board_cls):
    async def main():
        fb = await fake_board_cls().start()
        b = make_board(fb.port)
        await b.async_GetStatus()
        await b.async_GetConfig()
        await fb.stop()
        return b
    b = run(main())
    assert b._ModuleID == 'dS2824'
    assert (b._SystemFirmwareMajor, b._SystemFirmwareMinor) == (4, 13)
    assert (b._ApplicationFirmwareMajor, b._ApplicationFirmwareMinor) == (3, 8)
    assert b._Volts == 12.0
    assert b._Temperature == 26.7
    assert b._CustomFirmeware is True
    assert b._MACAddress == '0:1:2:ab:4:5'
    assert (b._PhysicalRelays, b._ConnectedLights, b._ConnectedShutters, b._ConnectedSockets,
            b._ConnectedMotionSensors, b._ConnectedButtons) == (24, 4, 3, 12, 1, 2)


def test_fragmented_responses_async_and_sync(fake_board_cls):
    async def main():
        fb = await fake_board_cls(fragment=True).start()
        a = make_board(fb.port)
        await a.async_GetStatus(); await a.async_GetConfig()
        s = make_board(fb.port)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, s.GetStatus)
        await loop.run_in_executor(None, s.GetConfig)
        await fb.stop()
        return a, s
    a, s = run(main())
    for b in (a, s):
        assert b._Temperature == 26.7
        assert b._ConnectedSockets == 12 and b._ConnectedButtons == 2


def test_requests_are_serialized(fake_board_cls):
    async def main():
        fb = await fake_board_cls().start()
        b = make_board(fb.port)
        await b.async_GetConfig()
        res = await asyncio.gather(*[b.async_GetLight(1) for _ in range(10)],
                                   *[b.async_SetLight(2, 'on') for _ in range(5)],
                                   *[b.async_GetShutter(1) for _ in range(5)])
        await fb.stop()
        return fb, res
    fb, res = run(main())
    assert fb.max_active == 1, 'board must never see parallel connections'
    assert res[:10] == ['on'] * 10
    assert res[10:15] == [True] * 5


def test_entity_getters(fake_board_cls):
    async def main():
        fb = await fake_board_cls().start()
        b = make_board(fb.port)
        await b.async_GetConfig()
        out = (await b.async_GetLight(2), await b.async_GetSocket(1), await b.async_GetMotion(1),
               await b.async_GetButton(1), await b.async_GetShutter(1))
        await fb.stop()
        return out
    light, socket_, motion, button, shutter = run(main())
    assert light == 'off'
    assert socket_ == 'on'
    assert motion == 'off'
    assert button == 3
    assert shutter is not None


def test_invalid_identifier_does_not_send(fake_board_cls):
    async def main():
        fb = await fake_board_cls().start()
        b = make_board(fb.port)
        await b.async_GetConfig()
        n = len(fb.requests)
        r = await b.async_GetLight(99)
        await fb.stop()
        return r, len(fb.requests) - n
    r, sent = run(main())
    assert r is None and sent == 0


def test_unresponsive_board_times_out(fake_board_cls):
    async def main():
        fb = await fake_board_cls(silent=True).start()
        b = make_board(fb.port, timeout=1)
        t = time.monotonic()
        r = await b.async_GetStatus()
        took = time.monotonic() - t
        fb.server.close()
        return b, r, took
    b, r, took = run(main())
    assert r is None
    assert b._SystemFirmwareMajor == 0
    assert took < 5, 'timeout + one retry must not hang'


def test_unreachable_board_fails_fast():
    async def main():
        b = make_board(1, timeout=1)  # nothing listens on port 1
        return await b.async_GetStatus(), b
    r, b = run(main())
    assert r is None and b._SystemFirmwareMajor == 0


def test_sync_unreachable_board():
    b = make_board(1, timeout=1)
    b.GetStatus()
    assert b._SystemFirmwareMajor == 0


def test_unknown_module_id(fake_board_cls):
    class Unknown(fake_board_cls):
        def response(self, cmd, arg):
            return bytes([99, 1, 1, 1, 1, 120, 0, 200]) if cmd == 0x30 else super().response(cmd, arg)
    async def main():
        fb = await Unknown().start()
        b = make_board(fb.port)
        await b.async_GetStatus()
        await fb.stop()
        return b
    b = run(main())
    assert b._ModuleID == 'Unknown (99)'
    assert b._SystemFirmwareMajor == 1
