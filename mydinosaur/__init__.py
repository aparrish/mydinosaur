import sqlite3
import datetime
from email.utils import formatdate
import uuid
from tempfile import mkdtemp
import os
import shutil
import imghdr

from jinja2 import Template
import PyRSS2Gen as RSS2
import dateutil.parser

html_template = """\
<!doctype html>
<html>
	<head>
		<title>{{ rss_title }}: {{ post_title }}</title>
		<link rel="stylesheet" href="dino-style.css">
	</head>
	<body>
		<header>
			<h1 class="post_title">{{ post_title }}</h1>
		</header>
		<div class="post_description">{{ post_description }}</div>
		<div class="enclosure">
		{% if enclosure_url %}
			{% if enclosure_media_type in ['image/png', 'image/gif', 'image/jpeg'] %}
				<img src="{{ enclosure_url }}">
			{% else %}
				<a href="{{ enclosure_url }}">View media</a>
			{% endif %}
		{% endif %}
		</div>
		<footer>
			<div class="rss_link"><a href="{{ rss_link }}">{{ rss_title }}</a></div>
			<div class="rss_feed_link"><a href="{{ rss_feed_link }}" rel="alternate"
				type="application/rss+xml">{{ rss_title }}</a></div>
			<div class="post_timestamp">{{ post_timestamp }}</div>
		</footer>
	</body>
	<!-- MyDinosaur default html template -->
</html>
"""

def totimestamp(dt):
	return (dt - datetime.datetime(1970, 1, 1)).total_seconds()

def ext_mime_type(ext):
	return {
			'png': 'image/png',
			'gif': 'image/gif',
			'jpeg': 'image/jpeg'}[ext]

def mime_type_ext(mime_type):
	return {
			'image/png': 'png',
			'image/gif': 'gif',
			'image/jpeg': 'jpeg'}[mime_type]

def guess_extension_and_media_type(fname, media_type=None, ext=None):
	if media_type is None:
		detected_type = imghdr.what(fname)
		media_type = ext_mime_type(detected_type)
	if ext is None:
		ext = mime_type_ext(media_type)
	return (ext, media_type)

class MyDinosaur(object):
	def __init__(self, connection, title, link, description,
			base_url, rss_filename="rss.xml", template=None, output_dir=None,
			**extra_args):
		self.extra_args = extra_args
		if isinstance(connection, basestring):
			self.connection = sqlite3.connect(connection)
		else:
			self.connection = connection
		if output_dir is None:
			output_dir = mkdtemp()
		self.output_dir = output_dir
		self.title = title
		self.link = link
		self.description = description
		self.base_url = base_url
		self.rss_filename = rss_filename
		if template is None:
			self.template = html_template
		else:
			self.template = template
		self.cursor = self.connection.cursor()
		self.cursor.execute("""
		create table if not exists posts (
			id integer primary key,
			text text,
			encl_url text,
			encl_media_type text,
			timestamp text)
		""")

	def update(self, status):
		self.add_item(status)
		self.files = self.generate_feed_items()
		self.transfer_files()
		return self.files

	def update_with_media(self, status, media, media_type=None, ext=None):
		fname = os.path.join(self.output_dir, str(uuid.uuid4()))
		with open(fname, "wb") as fh:
			fh.write(media.read())
		try:
			(ext, media_type) = guess_extension_and_media_type(fname, media_type, ext)
		except KeyError:
			raise KeyError(
				"Can't detect MIME type of media. Please specify with media_type "
				"and ext parameters.")
		fname_with_ext = fname + "." + ext
		os.rename(fname, fname_with_ext)
		basename = os.path.basename(fname_with_ext)
		self.add_item(status, self.base_url + basename, media_type)
		self.files = [fname_with_ext] + self.generate_feed_items()
		self.transfer_files()
		return self.files 

	def add_item(self, text, encl_url=None, encl_media_type=None):
		self.cursor.execute(
				"insert into posts(text, timestamp, encl_url, encl_media_type) " +
				"values (?, ?, ?, ?)", (text, datetime.datetime.utcnow().isoformat(),
					encl_url, encl_media_type))
		self.connection.commit()

	def generate_feed_items(self):
		self.cursor.execute("select * from posts order by timestamp desc limit 10")
		from_db = self.cursor.fetchall()
		posts = list()
		files = list()
		for (id_, text, enclosure_url, enclosure_media_type, timestamp) in from_db:
			post = RSS2.RSSItem(
					title=text,
					description=text,
					link=self.base_url + "%s.html" % id_,
					guid=RSS2.Guid(self.base_url + "%s.html" % id_),
					pubDate=formatdate(totimestamp(dateutil.parser.parse(timestamp))))
			if enclosure_url is not None:
				post.enclosure = RSS2.Enclosure(
						url=enclosure_url,
						type=enclosure_media_type,
						length=0)
			posts.append(post)
			html_output = Template(self.template).render(
					rss_title=self.title,
					rss_link=self.link,
					rss_description=self.description,
					rss_feed_link=self.base_url + self.rss_filename,
					post_title=text,
					post_description=text,
					post_timestamp=timestamp,
					post_id=id_,
					enclosure_url=enclosure_url,
					enclosure_media_type=enclosure_media_type)
			html_fname = os.path.join(self.output_dir, "%s.html" % id_)
			with open(html_fname, "wb") as fh:
				fh.write(html_output)
			files.append(html_fname)
		rss = RSS2.RSS2(
				title=self.title,
				link=self.link,
				description=self.description,
				lastBuildDate=datetime.datetime.utcnow(),
				items=posts)
		rss_fname = os.path.join(self.output_dir, self.rss_filename)
		rss.write_xml(open(rss_fname, "wb"))
		files.append(rss_fname)
		return files

	def transfer_files(self):
		"Unimplemented in base class."
		pass

	def clean_up(self):
		shutil.rmtree(self.output_dir)

class MyS3Dinosaur(MyDinosaur):
	def transfer_files(self):
		from boto.s3.connection import S3Connection
		from boto.s3.connection import Key
		conn = S3Connection(self.extra_args['aws_access_key'],
				self.extra_args['aws_secret_key'])
		bucket = conn.get_bucket(self.extra_args['s3_bucket'])
		for fname in self.files:
			key = Key(bucket)
			key.key = os.path.basename(fname)
			key.set_contents_from_filename(fname)

