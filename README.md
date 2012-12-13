[TeaScrum]
==========

TeaScrum is a web application for software development teams to use the Scrum methodology.


Prerequisite
------------

Python 2.7+
Django 1.3+
MySQL or PostgreSQL
Apache HTTP server

Installation
------------

+ Clone the repo, `git clone git://github.com/tea-scrum.git`, [download the latest release](https://github.com/tea-scrum/zipball/master).
+ Unzip the package into a subdirectory.

Database Preparation
--------------------

After the package is unzipped, create the database and the tables. In the unzipped folder where 'master.py' file exists, run the following commands in a console.
MySQL DBMS is used for example.

+ mysql -u root -e "CREATE DATABASE scrum CHARACTER SET 'utf8'"
+ mysql -u root -e "CREATE USER scrum IDENTIFIED BY 'scrum'"
+ mysql -u root -e "GRANT ALL ON scrum.* TO scrum@localhost IDENTIFIED BY 'scrum'"
+ python manage.py syncdb
+ python manage.py createsuperuser --username=scrum --email=scrum@example.com


Configuration
-------------

Edit settings.py file and modify the following settings accordingly:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'scrum',                      # Or path to database file if using sqlite3.
        'USER': 'scrum',                      # Not used with sqlite3.
        'PASSWORD': 'scrum',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}
TIME_ZONE = 'Asia/Shanghai'
LANGUAGE_CODE = 'zh-cn'


Start-Up
--------

Run the server using Django:
+ python manager.py runserver
Developers can run it in Eclipse or Aptana Studio.
+ Browse http://localhost:8000/
+ Login using the superuser 'scrum'
+ Let product owners and scrum masters register themselves
+ And add them to these groups after they're registered using the admin interface.
 

Create a Scrum Team
-------------------

+ Login to http://localhost:8000 with a product owner or scrum master
+ Create a product, assign a product owner and a scrum master as well as a team

Create a Product
----------------

+ Login as the product owner
+ Create a new product
+ Add backlog items one by one, or
+ Bulk input a list of items (user stories)
+ Set priorities for the user stories

Plan a Sprint
-------------

+ Login as the scrum master
+ Select a product to work on
+ Create a new sprint
+ Select a list of backlog items for the sprint
+ Add tasks for the items
+ Estimate effort for the taks and items with Planning poker game

Daily Scrum
-----------
+ Login as a team member and start a daily scrum with a taskboard.
+ Prepare a memo for the 3 daily scrum questions
+ Pick a task to work on at any time
+ View current working tasks and mark as finished when ready

Retrospective
-------------

+ Login as scrum master
+ Mark sprint as complete
+ Add retro during the meeting

Release Planning
----------------


Admin Site
----------
Login to http://localhost:8000/admin as the superuser, and modify any data entities as necessary.


Bug tracker
-----------

Have a bug? Please create an issue here on GitHub that conforms with [necolas's guidelines](https://github.com/necolas/issue-guidelines).



Blog
----

Read more detailed announcements, discussions, and more on [The TeaScrum Blog](http://).



Mailing list
------------

Have a question? Ask on our mailing list!

teascrum@googlegroups.com

http://groups.google.com/group/teascrum



Contributing
------------




Authors
-------

**Ted Wen**

+ http://twitter.com/tedwen
+ http://github.com/tedwen

License
-------

This software is released under the Apache License, Version 2.0.  See LICENSE file for details.
