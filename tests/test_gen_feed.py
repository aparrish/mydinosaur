import unittest
import os
import datetime

import feedparser
from dateutil.parser import parse
from dateutil.tz import tzutc
from datetime import datetime, timedelta

import mydinosaur

class TestGenFeed(unittest.TestCase):
	def test_generate_feed(self):
		title = "Dino Test"
		link = "http://example.com"
		description = "My dino test"
		base_url = "http://example.com/items/"
		dino = mydinosaur.MyDinosaur(':memory:',
				title=title,
				link=link,
				description=description,
				base_url=base_url)

		files = dino.update('this is a test!')
		files = dino.update('this is another test!')
		self.assertIn('rss.xml', [os.path.basename(f) for f in files])
		self.assertIn('1.html', [os.path.basename(f) for f in files])
		self.assertIn('2.html', [os.path.basename(f) for f in files])

		feed = feedparser.parse(
				[f for f in files if os.path.basename(f) == 'rss.xml'][0])
		self.assertEqual(feed['feed']['title'], title)
		self.assertEqual(feed['feed']['link'], link)
		self.assertEqual(feed['feed']['description'], description)

		self.assertEqual(len(feed.entries), 2)
		self.assertEqual(feed.entries[1].title, 'this is a test!')
		self.assertEqual(feed.entries[0].title, 'this is another test!')

		self.assertEqual(feed.entries[1].description, 'this is a test!')
		self.assertEqual(feed.entries[1].link, base_url + "1.html")

		# ensure that times are basically right
		self.assertLess(
				(parse(feed.entries[0].published) - datetime.now(tzutc())),
				timedelta(seconds=2))

		self.assertGreaterEqual(parse(feed.entries[0].published),
				parse(feed.entries[1].published))

	def test_update_with_media(self):
		from StringIO import StringIO
		title = "Dino Test"
		link = "http://example.com"
		description = "My dino test"
		base_url = "http://example.com/items/"
		dino = mydinosaur.MyDinosaur(':memory:',
				title=title,
				link=link,
				description=description,
				base_url=base_url)
		filehandle = StringIO("Hello there.\n")
		files = dino.update_with_media('this is a test!', filehandle,
				media_type="text/plain", ext="txt")
		self.assertIn('rss.xml', [os.path.basename(f) for f in files])
		self.assertIn('1.html', [os.path.basename(f) for f in files])
		self.assertEqual(len([fn for fn in files if fn.endswith('.txt')]), 1)

		text_file = [f for f in files if os.path.basename(f).endswith('.txt')][0]
		self.assertEqual(open(text_file).read(), "Hello there.\n")

		feed = feedparser.parse(
				[f for f in files if os.path.basename(f) == 'rss.xml'][0])
		self.assertEqual(len(feed.entries[0].enclosures), 1)
		self.assertEqual(feed.entries[0].enclosures[0]['type'], 'text/plain')
		self.assertEqual(feed.entries[0].enclosures[0]['url'],
				base_url + os.path.basename(text_file))

	def test_ext_mime_type(self):
		self.assertEqual("image/png", mydinosaur.ext_mime_type('png'))
		self.assertEqual("image/gif", mydinosaur.ext_mime_type('gif'))
		self.assertEqual("image/jpeg", mydinosaur.ext_mime_type('jpeg'))
		self.assertRaises(KeyError, mydinosaur.ext_mime_type, 'florb')

	def test_guess(self):
		gif_src = os.path.join(os.path.dirname(__file__), "test.gif")
		png_src = os.path.join(os.path.dirname(__file__), "test.png")
		jpeg_src = os.path.join(os.path.dirname(__file__), "test.jpeg")
		text_src = os.path.join(os.path.dirname(__file__), "test.txt")

		# ensure correct guesses for obvious media types
		self.assertEqual(('gif', 'image/gif'),
				mydinosaur.guess_extension_and_media_type(gif_src))
		self.assertEqual(('png', 'image/png'),
				mydinosaur.guess_extension_and_media_type(png_src))
		self.assertEqual(('jpeg', 'image/jpeg'),
				mydinosaur.guess_extension_and_media_type(jpeg_src))

		# unrecognized media type raises exception
		self.assertRaises(KeyError, mydinosaur.guess_extension_and_media_type,
				text_src)

		# override detection
		self.assertEqual(('txt', 'text/plain'),
				mydinosaur.guess_extension_and_media_type(text_src, 'text/plain',
					'txt'))

		# override extension
		self.assertEqual(('jpg', 'image/jpeg'),
				mydinosaur.guess_extension_and_media_type(jpeg_src, None,
					'jpg'))

		# correct extension for mime type even if mime type not specified
		self.assertEqual(('png', 'image/png'),
				mydinosaur.guess_extension_and_media_type(png_src, 'image/png'))

	def test_override_template(self):
		title = "Dino Test"
		link = "http://example.com"
		description = "My dino test"
		base_url = "http://example.com/items/"
		dino = mydinosaur.MyDinosaur(':memory:',
				title=title,
				link=link,
				description=description,
				base_url=base_url)
		files = dino.update('this is a test!')
		self.assertIn('1.html', [os.path.basename(f) for f in files])
		html_src = open([f for f in files if f.endswith('1.html')][0]).read()
		self.assertIn('<!-- MyDinosaur default html template -->', html_src)

		override_template = "<html>whatever</html>"
		dino = mydinosaur.MyDinosaur(':memory:',
				title=title,
				link=link,
				description=description,
				base_url=base_url,
				template=override_template)
		files = dino.update('this is a test!')
		self.assertIn('1.html', [os.path.basename(f) for f in files])
		html_src = open([f for f in files if f.endswith('1.html')][0]).read()
		self.assertEqual(override_template, html_src)
	
	def test_use_existing_sqlite_connection(self):
		import sqlite3
		conn = sqlite3.connect(':memory:')
		title = "Dino Test"
		link = "http://example.com"
		description = "My dino test"
		base_url = "http://example.com/items/"
		dino = mydinosaur.MyDinosaur(conn,
				title=title,
				link=link,
				description=description,
				base_url=base_url)
		files = dino.update('this is a test!')
		self.assertIn('rss.xml', [os.path.basename(f) for f in files])
		self.assertIn('1.html', [os.path.basename(f) for f in files])

if __name__ == '__main__':
	unittest.main()
