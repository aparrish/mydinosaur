#My Dinosaur

> "The first time you told that [joke about RSS being dead] I laughed so hard I
> fell off my dinosaur and broke my igneous thong."---Chucklebot (paraphrased)

*NOTE*: This library is still in the early stages of development and might be
broken in horrible ways, or not even work at all! Use at your own risk.

My Dinosaur is a fun library for bot makers to create RSS feeds for their bots.
The idea is to mimic, as much as possible, the ease-of-use of posting a
status update to Twitter.

But why? Because no one knows what tomorrow may bring! RSS is an open standard.
Let us use it as a bulwark against the fickle minds and monies of monolithic
platforms (like Twitter) that may not always be working in our best interests.

##Installation

Someday this will be an actual package and there will be installation
instructions here. Until then, just clone the repository and copy the
`mydinosaur` directory where your Python program can see it. The required
packages are listed in `requirements.txt`; you can install them like so:

	$ pip install -r requirements.txt

(Make a virtualenv first!)

##Usage

Here's the simplest use case:

	from mydinosaur import MyDinosaur
	dino = MyDinosaur('posts.sql',
			title="My Feed",
			link="http://example.com/",
			description="Hooray for my feed!",
			base_url="http://example.com/items/")
	files = dino.update('this is a test!')

The `.update()` method returns a list of files that need to be uploaded
somewhere. (The build process puts these files in a temporary directory, unless
overridden with the `output_dir` parameter.) You can use whatever program you'd
like to upload those files to a server---all the server has to be able to do is
serve static files.

Information about posts that you've made is persisted in a SQLite database
(named in the first parameter to `MyDinosaur`'s `__init__` method). The RSS
feed is generated from the last ten posts in reverse chronological order.

Individual HTML pages are made for each post and uploaded to the same location
as the RSS feed. The files reference a stylesheet, `dino-style.css`, which is
not included but which you can write and upload.

The HTML is generated from a Jinja2 template; you can specify your
own template string in the constructor:

	dino = MyDinosaur('posts.sql', template='<html>hooray!</html>')

(See the `.generate_feed_items()` method for more information on which
variables get passed to the template.)

##Updating with media

There's also an `.update_with_media()` method:

	files = dino.update_with_media('this is a test!', open('foo.png'))

... which will create a post with the file embedded and also include a copy of
the file in the files to be uploaded. (Note: unlike the text of an update, the
media files are NOT stored in the database, and are only included in the update
list when you first create them.)

The `.update_with_media()` method needs the MIME-type of the file in order
to attach it to the RSS feed. For most common image types, it guesses the
MIME-type and file extension correctly, but for other kinds of files you
may need to specify it explicitly, like so:

	files = dino.update_with_media('whatever', open('foo.txt'),
			media_type="text/plain", ext="txt")

##Special dinosaurs

A special dinosaur, `MyS3Dinosaur`, will automatically upload the files to an
S3 bucket:

	from mydinosaur import MyS3Dinosaur
	dino = MyS3Dinosaur('posts.sql',
			title="My Feed",
			link="http://example.com/",
			description="Hooray for my feed!",
			aws_access_key="XXX",
			aws_secret_key="YYY",
			s3_bucket="foo")
	
	dino.update_with_media('this is a test!', open('foo.png'))

The AWS credentials should have permission to add and update keys in the named
bucket. If you want other people to be able to see your feed, you'll need to
change permissions on the files to make them readable by all; one strategy for
doing this is to [make a bucket
policy](http://tiffanybbrown.com/2014/09/making-all-objects-in-an-s3-bucket-public-by-default/index.html).

##Bugs and to-do list

* Make all this into an actual pip-compatible package
* Dinosaur for SFTP uploads (with paramiko?) 
* Actual documentation (API methods and template variables)
* Some more examples (code, templates, CSS stylesheets)
* Better clean-up of generated files (there's a `.clean_up()` method but it's unclear whether it should be called automatically?)

