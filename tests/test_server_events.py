"""Tests for dScriptServer (receiving firmware triggers) and event handling."""
import asyncio
import socket
import time

from conftest import run
from dScriptModule import dScriptBoard, dScriptServer


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def test_event_handlers_are_per_instance():
    a = dScriptBoard('127.0.0.1', 1)
    b = dScriptBoard('127.0.0.1', 1)
    calls = []
    handler = lambda sender, earg: calls.append(sender.topic)
    a.addEventHandler('light', handler)
    a.addEventHandler('light', handler)  # duplicate registration is ignored
    assert a._GetEventHandlers()['light'] == [handler]
    assert b._GetEventHandlers()['light'] == []
    assert dScriptBoard._EventHandlers['light'] == []
    a._throwEvent('x', 'light', 1, 'on')
    b._throwEvent('x', 'light', 1, 'on')
    assert calls == ['light']
    a.removeEventHandler('light', handler)
    a.removeEventHandler('light', handler)  # removing twice does not raise
    assert a._GetEventHandlers()['light'] == []


async def send_triggers(port, messages):
    for msg in messages:
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        writer.write(msg)
        await writer.drain()
        writer.write_eof()  # like a finished firmware write - an empty message then reaches the server as EOF
        await reader.read(10)  # server closes the connection after reading
        writer.close()
    await asyncio.sleep(0.2)


EXPECTED = [('getlight', 2, 'on'), ('heartbeat', None, None), ('getshutter', 1, 55), ('getlight', 3, None), ('getbutton', 1, 2)]
MESSAGES = [bytes([81, 2, 1]), bytes([0, 0, 255]), bytes([82, 1, 55]), bytes([81, 3, 255]),
            bytes([99, 1, 1]), b'', bytes([85, 1, 2])]  # unknown command and empty message must be ignored


def register(server, events):
    handler = lambda sender, earg: events.append((sender.topic, sender.identifier, sender.value))
    for topic in ('getlight', 'heartbeat', 'getshutter', 'getbutton'):
        server.addEventHandler(topic, handler)


def test_async_server_receives_triggers_and_restarts():
    async def main():
        port = free_port()
        events = []
        ds = dScriptServer('127.0.0.1', port)
        register(ds, events)
        await ds.async_StartServer()
        assert ds.State is True
        await send_triggers(port, MESSAGES)
        await ds.async_StopServer()
        assert ds.State is False
        await ds.async_StartServer()  # restart after stop must work
        restarted = ds.State
        await ds.async_StopServer()
        return events, restarted
    events, restarted = run(main())
    assert events == EXPECTED
    assert restarted is True


def test_sync_server_receives_all_bytes_and_stops():
    port = free_port()
    events = []
    ds = dScriptServer('127.0.0.1', port)
    register(ds, events)
    ds.StartServer()
    for _ in range(50):
        if ds.State: break
        time.sleep(0.05)
    assert ds.State is True
    run(send_triggers(port, MESSAGES))
    ds.StopServer()
    assert ds.State is False
    assert sorted(events, key=str) == sorted(EXPECTED, key=str)
