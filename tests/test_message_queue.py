import unittest
from datatransfer.storage import MessageQueue, create_mq
from unittest.mock import MagicMock

class TestMessageQueue(unittest.TestCase):
    def setup(self):
        self.conf = {'username': 'user',
                     'password': 'password',
                     'host': 'rabbitmq',
                     'port': '5672',
                     'max_retries': 10,
                     'queue_name': 'a_test_queue'}
        self.pika = MagicMock()
        self.pika.PlainCredentials.return_value = True
        connection = MagicMock()
        self.channel = MagicMock()
        self.channel.basic_publish.return_value = True
        connection.channel.return_value = self.channel
        self.pika.BlockingConnection.return_value = connection

    def test_connection_establish_auth(self):
        self.setup()
        mq = MessageQueue(self.conf, pika=self.pika)
        self.pika.PlainCredentials.assert_called()
        self.assertIsNotNone(mq.channel())

    def test_connection_establish_no_auth(self):
        self.setup()
        conf = {'host': 'rabbitmq', 'port': '5672', 'queue_name': 'a'}
        mq = MessageQueue(conf, pika=self.pika)
        self.pika.PlainCredentials.assert_not_called()
        self.assertIsNotNone(mq.channel())

    def test_event_publish(self):
        self.setup()
        mq = MessageQueue(self.conf, pika=self.pika)
        self.assertTrue(mq.publish_event('an_event'))
        self.channel.basic_publish.assert_called()

    def test_event_publish_nack(self):
        self.setup()
        self.channel.basic_publish.return_value = False
        mq = MessageQueue(self.conf, pika=self.pika)
        with self.assertRaises(RuntimeError):
            mq.publish_event('an_event')

    def test_create_mq(self):
        mq = create_mq()
        self.assertIsNotNone(mq.channel())


if __name__ == "__main__":
    unittest.main()
