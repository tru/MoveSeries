#!/usr/bin/python
#
# Licensed under LGPL
# By Tobias Hieta <tobias@hieta.se>
#

from optparse import OptionParser
import os
import logging
import sys
import re
import shutil

log = logging.getLogger("serie-mover")

class SeriesMover:
    def __init__(self, args):
        self.dest = args.destination_dir
        self.source = args.source_dir
        self.dry_run = args.dry_run
        self.noseason = args.noseason
        self.subtitles = args.subtitles
        self._dest_directories = []
        
        self.moviefile_re = re.compile(".+\.(mkv|avi|mpg|m4v)", re.I)
        self.season_re = re.compile(".+s(\d+)e(\d+)", re.I)

    def _scan_dest(self):
        log.debug("scanning destination dir")
        for p in os.listdir(self.dest):
            path = os.path.join(self.dest, p)
            if (os.path.isdir(path)):
                log.debug("adding %s as a destination", p)
                self._dest_directories.append(p)
                
    def _scan_source(self):
        log.debug("scanning source for matching files")
        for p in os.listdir(self.source):
            path = os.path.join(self.source, p)
            
            # make sure we have a file
            if not os.path.isfile(path):
                log.debug("Skipping non-file %s", path)
                continue
            
            # check if the file is actually ending with a movie extension
            if not self.moviefile_re.match(p):
                log.debug("%s didn't match the mofilefile regexp, skipping")
                continue
            
            # checking the start of the filename with our directories. this could be
            # expanded to check for series starting with 'the' and similar.
            dest_dir = None
            log.debug("evaluating %s", p)
            for dest in self._dest_directories:
                if p.lower().startswith(dest.lower()):
                    log.debug("%s seems to match directory %s", p, dest)
                    dest_dir = os.path.join(self.dest, dest)
            
            # matching season
            season = -1
            match = False
            if not (self.noseason):
                match = self.season_re.match(p)
            if match:
                try:
                    season = int(match.group(1))
                except:
                    log.warning("Couldn't convert %s to integer, can't determine season", match.group(1))
                    season = -1
            else:
                log.info("Couldn't match season, or disabled, will just use top directory!")
                season = -1
                
            final_dir = dest_dir
            if not (season == -1):
                final_dir = os.path.join(dest_dir, "season." + str(season))
                
            log.info("will move %s to %s", p, final_dir)
            if not self.dry_run:
                if not (os.path.isdir(final_dir)):
                    log.debug("creating directory %s" % final_dir)
                    try:
                        os.makedir(final_dir)
                    except:
                        log.error("couldn't create directory %s, will exit now" % final_dir)
                        sys.exit(-1)
                    
                
                try:
                    shutil.move(path, os.path.join(final_dir, p))
                except:
                    log.error("couldn't move %s to directory %s, will exit now", path, final_dir)
                    sys.exit(-1)
        
    def run(self):
        log.info("Looking for series in %s to move to %s (dry_run = %d, subtitles = %d)" % (self.source, self.dest, self.dry_run, self.subtitles))
        self._scan_dest()
        self._scan_source()


def check_is_dir(option, opt_str, value, parser):
    if os.path.isdir(value):
        setattr(parser.values, option.dest, value)
        log.debug("setting destdir to %s", value)
    else:
        log.error("-d/--dest must be an existing directory")

if __name__=='__main__':
    parser = OptionParser()
    parser.add_option('-d', '--dest-dir', type="string", action="callback", callback=check_is_dir, dest="destination_dir", help='destination dir - where we should put the series')
    parser.add_option('-s', '--source-dir', type="string", action="callback", callback=check_is_dir, dest="source_dir", help='source dir - where we should look for new series')
    parser.add_option('-r', '--dry-run', action="store_true", dest='dry_run', help='make a dry-run, just show me what you are going to do', default=False)
    parser.add_option('', '--subtitles', action="store_true", dest='subtitles', help='try to automatically download subtitles', default=False)
    parser.add_option('-v', '--verbose', action="store_true", dest="verbose", help="Display debug information", default=False)
    parser.add_option('', '--disable-season', action="store_true", dest="noseason", help="Disable season matching", default=False)
    (options, args) = parser.parse_args()
    
    if (parser.values.verbose):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    
    if (not (parser.values.destination_dir) or not (parser.values.source_dir)):
        log.error("Need to define both destination and source directory!")
        sys.exit(-1)
    
    mover = SeriesMover(parser.values)
    mover.run()

