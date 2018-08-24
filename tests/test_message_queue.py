import unittest
from datatransfer.storage import MessageQueue
from unittest.mock import MagicMock

class TestMessageQueue(unittest.TestCase):
    def test_connection_establish(self):
        conf = {'username': 'user',
                'password': 'password',
                'host': 'rabbitmq',
                'port': '5672',
                'queue_name': 'a_test_queue'}
        mq = MessageQueue(conf)
        self.assertIsNotNone(mq.channel())

if __name__ == "__main__":
    unittest.main()
