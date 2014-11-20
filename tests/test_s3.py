import unittest
import os
import datetime
from urlparse import urlparse
from StringIO import StringIO

import feedparser
from boto.s3.connection import S3Connection
from boto.s3.connection import Key

import mydinosaur

class TestS3(unittest.TestCase):

	def test_s3(self):
		title = "Dino Test"
		link = "http://example.com"
		description = "My dino test"
		base_url = "http://example.com/items/"
		aws_key = os.environ['MYDINOSAUR_AWS_ACCESS_KEY']
		aws_secret = os.environ['MYDINOSAUR_AWS_SECRET_KEY']
		s3_bucket = os.environ['MYDINOSAUR_S3_BUCKET']
		dino = mydinosaur.MyS3Dinosaur(':memory:',
				title=title,
				link=link,
				description=description,
				base_url=base_url,
				aws_access_key=aws_key,
				aws_secret_key=aws_secret,
				s3_bucket=s3_bucket)
		dino.update("hello there")

		# make sure that stuff got uploaded
		conn = S3Connection(aws_key, aws_secret)
		bucket = conn.get_bucket(s3_bucket) 

		k = Key(bucket)
		k.key = 'rss.xml'
		feed = feedparser.parse(k.get_contents_as_string())
		self.assertEqual(len(feed.entries), 1)

		k = Key(bucket)
		k.key = '1.html'
		html = k.get_contents_as_string()
		self.assertIn('<!-- MyDinosaur default html template -->', html)

		# now, update with media!
		filehandle = StringIO("Hello there.\n")
		dino.update_with_media('this is a test', filehandle,
				media_type="text/plain", ext="txt")

		k = Key(bucket)
		k.key = 'rss.xml'
		feed = feedparser.parse(k.get_contents_as_string())
		self.assertEqual(len(feed.entries), 2)

		# ensure that media was uploaded
		media_url = feed.entries[0].enclosures[0].url
		key_name = urlparse(media_url).path.split('/')[-1]
		k = Key(bucket)
		k.key = key_name
		contents = k.get_contents_as_string()
		self.assertEqual(contents, "Hello there.\n")

if __name__ == '__main__':
	unittest.main()

