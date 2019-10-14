import json
import os
import threading
import time
import unittest

import requests
import websocket as ws

RECEIVER_URL = os.getenv('RECEIVER_URL')
WEBSOCKET_URL = os.getenv('WEBSOCKET_URL')
INTERVAL = int(os.getenv('INTERVAL'))

TIMEOUT = 10.0


class WebsocketTestCase(unittest.TestCase):
    def test_receiver(self):
        response = requests.post(RECEIVER_URL, json={"cpu": 1.0})
        self.assertEqual(response.status_code, 200)

    def test_ws_connection(self):
        sock = ws.WebSocket()
        self.assertEqual(sock.connected, False)
        sock.connect(WEBSOCKET_URL + '?topics=cpu')
        self.assertEqual(sock.connected, True)
        sock.close()

    def test_receiver_and_websocket(self):
        socket_connected = threading.Event()
        socket_closed_error = threading.Event()
        sock = ws.WebSocket()

        def run_websocket():
            sock.connect(WEBSOCKET_URL + '?topics=gpu')
            socket_connected.set()
            try:
                for msg in sock:
                    value = json.loads(msg)['gpu']
                    self.assertEqual(value, 12345.0,
                                     f"Expected gpu value is 12345.0, instead got {value}")
                    break
            except ws.WebSocketConnectionClosedException:
                socket_closed_error.set()
            sock.close()
        ws_thread = threading.Thread(target=run_websocket)
        ws_thread.start()
        if socket_connected.wait(TIMEOUT):
            requests.post(RECEIVER_URL, json={"gpu": 12345.0})
        ws_thread.join(TIMEOUT)
        if ws_thread.is_alive():
            sock.abort()
            if socket_closed_error.wait(TIMEOUT):
                self.assertTrue(False, "Expected at least one frame on gpu topic, but got none")

    def test_generator_data_receiving(self):
        msg_count_to_wait = 5
        socket_closed_error = threading.Event()
        sock = ws.WebSocket()

        def run_websocket():
            sock.connect(WEBSOCKET_URL + '?topics=cpu')
            counter = 0
            try:
                for _ in sock:
                    counter += 1
                    if counter == msg_count_to_wait:
                        break
            except ws.WebSocketConnectionClosedException:
                socket_closed_error.set()
            sock.close()

        ws_thread = threading.Thread(target=run_websocket)
        time_ = time.time()
        ws_thread.start()
        ws_thread.join(INTERVAL * msg_count_to_wait)
        if ws_thread.is_alive():
            sock.abort()
            if socket_closed_error.wait(TIMEOUT):
                self.assertTrue(False, f"Expected at least {msg_count_to_wait} frames on cpu topic in "
                                       f"{INTERVAL * msg_count_to_wait} seconds window")
        time_passed = time.time() - time_
        self.assertGreaterEqual(int(time_passed / INTERVAL) + 1, msg_count_to_wait,
                                f"Received messages count is lesser then expected ({msg_count_to_wait} messages) "
                                f"using time interval between messages equal to {INTERVAL} seconds.")


if __name__ == '__main__':
    unittest.main()
