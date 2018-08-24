import unittest
from datatransfer.storage import MessageQueue
from unittest.mock import MagicMock

class TestMessageQueue(unittest.TestCase):
    def setup(self):
        self.conf = {'username': 'user',
                     'password': 'password',
                     'host': 'rabbitmq',
                     'port': '5672',
                     'queue_name': 'a_test_queue'}
        self.pika = MagicMock()
        connection = MagicMock()
        self.channel = MagicMock()
        self.channel.basic_publish.return_value = True
        connection.channel.return_value = self.channel
        self.pika.BlockingConnection.return_value = connection
        self.mq = MessageQueue(self.conf, pika=self.pika)

    def test_connection_establish(self):
        self.setup()
        mq = MessageQueue(self.conf)
        self.assertIsNotNone(mq.channel())

    def test_event_publish(self):
        self.setup()
        self.assertTrue(self.mq.publish_event('an_event'))
        self.channel.basic_publish.assert_called()

if __name__ == "__main__":
    unittest.main()
