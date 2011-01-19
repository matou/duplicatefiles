import os,sys,hashlib,logging

# init logging
logging.basicConfig(level=logging.DEBUG)

def process_file(path):
    "returns a tuple (hashsum, size)"
    f = open(path)
    md5 = hashlib.md5()
    while True:
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
        f = curdir + os.sep + f
        if os.path.isfile(f):
            key = process_file(f)
            if not files.has_key(key):
                files[key] = []
            files[key].append(f)
            filecounter += 1
        elif os.path.isdir(f):
            dirs.append(f)
        # else ignore (if neither file nor directory, e.g. symlink)

logging.info("found %d files" % filecounter)
logging.debug(files)
