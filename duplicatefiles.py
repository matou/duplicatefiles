import os,sys,hashlib,logging

# init logging
level = logging.INFO
# very verbose output?
SPAM = False

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

logging.basicConfig(level=level)

def spam(msg):
    if SPAM:
        logging.debug("SPAM:%s" % msg)

logging.debug("threshold is %d" % threshold)

def hash_file(path):
    "returns hashsum as string"
    spam("hashing %s" % path)
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
    return md5.hexdigest()
    
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
            if os.path.getsize(f) <= threshold:
                spam("ignored %s" % f)
                continue
            key = os.path.getsize(f)
            if not files.has_key(key):
                files[key] = []
            files[key].append(f)
            filecounter += 1
            # debug
            if filecounter%10000 == 0:
                logging.debug("found %d files" % filecounter)
            # end debug
        elif os.path.isdir(f):
            dirs.append(f)
        # else ignore (if neither file nor directory, e.g. symlink)

logging.info("found %d files bigger than %d bytes" % (filecounter, threshold))

same = {}
# hash files that are of same size
filecounter = 0
sizes = files.keys()
for size in sizes:
    if len(files[size]) > 1:
        for f in files[size]:
            hashsum = hash_file(f)
            if not same.has_key((size, hashsum)):
                same[(size,hashsum)] = []
            same[(size,hashsum)].append(f)
            filecounter += 1
            if filecounter%100 == 0:
                logging.debug("hashed %d files" % filecounter)
    files.pop(size)

# output the result
for key in same:
    if len(same[key]) > 1:
        print "these files are the same: ",
        for f in same[key]:
            print "%s, " % f,
        print ""
