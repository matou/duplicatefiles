#!/usr/bin/python3

#
# Copyright (c) 2011 Matthias Matousek <matou@taunusstein.net>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
# 
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
# 

import os,sys,hashlib,logging,sqlite3,random

# init logging
level = logging.INFO
# very verbose output?
SPAM = False
# a database file to store the huge amount of data that will be gathered
database = "/tmp/dupfdb.%d" % random.randint(0,2**32)

# files that are smaller than the threshold will be ignored
threshold = 1024

loglevel = {"debug":logging.DEBUG,"info":logging.INFO,"warning":logging.WARNING, 
        "error":logging.ERROR,"fatal":logging.FATAL,"spam":logging.DEBUG}

# parse arguments:
for i in range(len(sys.argv)):
    if sys.argv[i] == "-l":
        level = loglevel[sys.argv[i+1].lower()]
        if sys.argv[i+1].lower() == "spam":
            SPAM = True
    if sys.argv[i] == "-t":
        threshold = int(sys.argv[i+1])
    if sys.argv[i] == "-d":
        database = sys.argv[i+1]

logging.basicConfig(level=level)

# connect to the database
dbconnection = sqlite3.connect(database)
db = dbconnection.cursor()
# create tables for the data
db.execute("CREATE TABLE files (size INTEGER, path TEXT)")
db.execute("CREATE TABLE same (tag TEXT, path TEXT)")

def spam(msg):
    if SPAM:
        logging.debug("SPAM:%s" % msg)

logging.debug("threshold is %d" % threshold)

def hash_file(path):
    "returns hashsum as string"
    spam("hashing %s" % path)
    f = open(path, mode="rb")
    md5 = hashlib.md5()
    while True:
        # do NOT load the whole file into memory
        # whole files in memory aren't kewl
        byte = f.read(10*1024)
        if not byte:
            break
        md5.update(byte)
    f.close()
    return md5.hexdigest()
    
# first collect all files that aren't directories or symlinks
logging.info("searching for files in current directory ('%s')" 
        % os.path.abspath(os.curdir))

# don't store this in the database. hopefully we won't have so many directories
# that the programm will run out of memory
dirs = [os.curdir]

# this dictionary is replaced by the files table in the database
#files = {}

filecounter = 0
while len(dirs) > 0:
    curdir = dirs.pop()
    spam("curdir: %s" % curdir)
    for f in os.listdir(curdir):
        spam("type(f): %s" % type(f))
        f = curdir + os.sep + f
        spam("f: %s" % str(os.path.abspath(f)))
        if os.path.islink(f):
            # don't bother us with links *grrr*
            spam("ignoring link: %s" % f)
            continue
        if os.path.isfile(f):
            size = os.path.getsize(f)
            if size <= threshold:
                spam("ignored %s" % f)
                continue
            try:
                db.execute("INSERT INTO files VALUES(?, ?)", (size, f))
            except UnicodeDecodeError:
                logging.error("%s caused a UnicodeDecodeError. Ignoring and moving on." % f)

            filecounter += 1
            # debug
            spam("found %d files" % filecounter)
            if filecounter%10000 == 0:
                dbconnection.commit()
                logging.debug("found %d files" % filecounter)
            # end debug
        elif os.path.isdir(f):
            dirs.append(f)
        # else ignore (if neither file nor directory, e.g. symlink)

dbconnection.commit()

logging.info("found %d files bigger than %d bytes" % (filecounter, threshold))
logging.info("starting hashing of files")

# replaced by table same
# same = {}
count = 0
cur = dbconnection.cursor()
cur.execute("SELECT DISTINCT size FROM files")

while True:
    row = cur.fetchone()
    if not row:
        break
    size = row[0]
    db.execute("SELECT * FROM files WHERE size=%d" % size)
    entries = db.fetchall()
    if len(entries) < 2:
        continue
    for entry in entries:
        try:
            db.execute("INSERT INTO same VALUES (?, ?)", 
                    ("%d:%s" % (size, hash_file(entry[1])), entry[1]))
        except UnicodeEncodeError:
            logging.error("%s caused a UnicodeEncodeError. That sucks! Trying to continue anyway." % entry[1])
        count += 1
        spam("processed %d files" % count)
        if count%1000 == 0:
            logging.debug("processed %d files" % count)
            dbconnection.commit()

dbconnection.commit()
logging.info("done hashing")
logging.info("looking for duplicates")
db.execute("SELECT DISTINCT tag FROM same AS s WHERE (SELECT COUNT(tag) FROM same as s2 where s2.tag=s.tag)>1")
tags = db.fetchall()
for tag in tags:
    db.execute("SELECT path FROM same WHERE tag='%s'" % tag[0])
    print("these files are the same: "),
    for path in db:
        print("%s," % path[0]),
    print("")

logging.info("END OF LINE")
