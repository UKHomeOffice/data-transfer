import unittest
from datatransfer.storage import MessageQueue, create_mq
from unittest.mock import MagicMock
from datatransfer import settings

class TestMessageQueue(unittest.TestCase):
    def setup(self):
        self.conf = {'username': settings.READ_MQ_USERNAME,
                     'password': settings.READ_MQ_PASSWORD,
                     'host': settings.READ_MQ_HOST,
                     'port': settings.READ_MQ_PORT,
                     'max_retries': settings.MAX_RETRIES,
                     'queue_name': settings.READ_MQ_PATH}
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
        conf = {'host': settings.READ_MQ_HOST,
                'port': settings.READ_MQ_PORT,
                'queue_name': settings.READ_MQ_PATH}
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
        self.setup()
        mq = create_mq("write")
        self.assertIsNotNone(mq.channel())

    def test_create_mq_non_readwrite(self):
        with self.assertRaises(ValueError):
            mq= create_mq('fail')

    def test_consumption(self):
        self.setup()
        self.channel.basic_consume = MagicMock()
        self.channel.start_consuming = MagicMock()
        callback = MagicMock()
        mq = MessageQueue(self.conf, pika=self.pika)
        mq.consume(callback)
        self.channel.basic_consume.assert_called_with(callback, queue=self.conf["queue_name"])
        self.channel.start_consuming.assert_called()


if __name__ == "__main__":
    unittest.main()
