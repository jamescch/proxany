import unittest
from socket import *

from httpparser import get_host_from_header


class TestProxyFwd(unittest.TestCase):

	# def setUp(self):
	# 	self.handler = Handler(None, 3128)

	def test_get_host_from_header(self):
		header = 'GET http://abcd HTTP/1.1\r\nHost: test.com\r\n\r\n'
		self.assertEqual(get_host_from_header(header), ('test.com', 80))


if __name__ == '__main__':
	unittest.main()
