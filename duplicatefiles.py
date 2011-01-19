import os,sys,hashlib,logging

# init logging
logging.basicConfig(level=logging.DEBUG)

# very verbose output?
SPAM = True

def spam(msg):
    if SPAM:
        logging.debug(msg)

# processed byte
pb = 0

def process_file(path):
    "returns a tuple (hashsum, size)"
    spam("processing %s" % path)
    f = open(path)
    md5 = hashlib.md5()
    while True:
        # do NOT load the whole file into memory:
        byte = f.read(1)
        if not byte:
            break
        md5.update(byte)
    f.close()
    return (md5.hexdigest(), os.path.getsize(path))
    
# first collect all files that aren't directories or symlinks
logging.info("searching for files in current directory ('%s')" 
        % os.path.abspath(os.curdir))
dirs = [os.curdir]
# will contain all the files by their hashsum/size
# TODO: put this in a database instead of having it in memory
files = {}

filecounter = 0
while len(dirs) > 0:
    curdir = dirs.pop()
    for f in os.listdir(curdir):
        # debugging
        spam("processed %d KB" % (pb/1024))
        if filecounter%101 == 100:
            logging.debug("processed %d files" % filecounter)
        f = curdir + os.sep + f
        if os.path.isfile(f):
            key = process_file(f)
            if not files.has_key(key):
                files[key] = []
            files[key].append(f)
            filecounter += 1
            pb += os.path.getsize(f)
        elif os.path.isdir(f):
            dirs.append(f)
        # else ignore (if neither file nor directory, e.g. symlink)

logging.info("found %d files" % filecounter)
logging.debug(files)

# output the result
for key in files:
    if len(files[key]) > 1:
        print "these files are the same: ",
        for f in files[key]:
            print "%s, " % f,
        print ""
