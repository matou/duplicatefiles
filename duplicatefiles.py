import os,sys,hashlib,logging

# init logging
logging.basicConfig(level=logging.DEBUG)

# very verbose output?
SPAM = False

# files that are smaller than the threshold will be ignored
threshold = 1024

def spam(msg):
    if SPAM:
        logging.debug(msg)

def process_file(path):
    "returns a tuple (hashsum, size)"
    spam("processing %s" % path)
    f = open(path)
    md5 = hashlib.md5()
    while True:
        # do NOT load the whole file into memory
        # whole files in memory aren't kewl
        byte = f.read(10*1024)
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
        f = curdir + os.sep + f
        if os.path.isfile(f):
            if os.path.getsize(f) < threshold:
                spam("ignored %s" % f)
                continue
            key = process_file(f)
            if not files.has_key(key):
                files[key] = []
            files[key].append(f)
            filecounter += 1
            # debug
            if filecounter%100 == 0:
                logging.debug("processed %d files" % filecounter)
            # end debug
        elif os.path.isdir(f):
            dirs.append(f)
        # else ignore (if neither file nor directory, e.g. symlink)

logging.info("found %d files bigger than %d bytes" % (filecounter, threshold))

# output the result
for key in files:
    if len(files[key]) > 1:
        print "these files are the same: ",
        for f in files[key]:
            print "%s, " % f,
        print ""
