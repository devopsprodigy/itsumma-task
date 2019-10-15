import os
import random
import string
import unittest

import requests

from dotenv import load_dotenv
load_dotenv()

RECEIVER_URL = os.getenv('RECEIVER_URL')
WEB_SERVER_URL = os.getenv('WEB_SERVER_URL')
INTERVAL = int(os.getenv('INTERVAL'))

TIMEOUT = 10.0


class WebsocketTestCase(unittest.TestCase):
    def test_receiver(self):
        response = requests.post(RECEIVER_URL, json={"cpu": 1.0})
        self.assertEqual(response.status_code, 200)

    def test_web_server(self):
        response = requests.get(WEB_SERVER_URL + '?topics=cpu')
        data = response.json()
        self.assertEqual(len(data.keys()), 1, "Expected only cpu key in response")
        self.assertIn('cpu', data.keys(), "Expected cpu key in response")
        self.assertEqual(type(data['cpu']), float, "cpu load value should be float")

    def test_receiver_and_server(self):
        random_topic = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        random_value = random.random() * 100
        requests.post(RECEIVER_URL, json={random_topic: random_value})
        response = requests.get(WEB_SERVER_URL + f'?topics={random_topic}')
        data = response.json()
        self.assertEqual(len(data.keys()), 1, f"Expected only {random_topic} key in response")
        self.assertIn(random_topic, data.keys(), f"Expected {random_topic} key in response")
        value = data[random_topic]
        self.assertEqual(value, random_value,
                         f"Expected {random_topic} value is {random_value}, instead got {value}")


if __name__ == '__main__':
    unittest.main()
