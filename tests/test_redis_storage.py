
import unittest
from datatransfer.storage import RedisStorage
from unittest.mock import MagicMock

class TestRedisStorage(unittest.TestCase):
    def setup(self):
        self.redis = MagicMock()
        self.redis_obj = MagicMock()
        self.redis_obj.lrange.return_value = [b'ke', b'ke']
        self.redis_obj.rpush.return_value = 1
        self.redis_obj.lrem.return_value = None
        self.redis.Redis = MagicMock(return_value = self.redis_obj)
        self.redis_storage = RedisStorage({'path':'foo'}, redis=self.redis)

    def test_list_dir(self):
        self.setup()
        assert self.redis_storage.list_dir() == [b'ke', b'ke']
        self.redis_obj.lrange.assert_called()

    def test_write_file(self):
        self.setup()
        self.redis_storage.write_file('aaa')
        self.assertIsNone(self.redis_storage.write_file('aaa'))
        self.redis_obj.rpush.assert_called_with('foo', 'aaa')

    def test_delete_file(self):
        self.setup()
        self.redis_storage.delete_file('aaa')
        self.assertIsNone(self.redis_storage.delete_file('aaa'))
        self.redis_obj.lrem.assert_called_with('foo', 'aaa')

if __name__ == "__main__":
    unittest.main()
