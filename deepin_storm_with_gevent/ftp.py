#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import gevent module before any other modules.
from patch import gevent_patch
gevent_patch()

import gevent
from gevent import GreenletExit

from ftplib import FTP
import traceback
import sys
import urlparse

class FetchFtp(object):
    '''
    class docs
    '''
	
    def __init__(self, file_url):
        '''
        init docs
        '''
        self.file_url = file_url
        
    def get_file_size(self):
        try:
            url = urlparse.urlparse(self.file_url)
            ftp = FTP(url[1])
            ftp.login()
            size = int(ftp.size(url[2]))
            ftp.quit()
            
            return size
        except Exception, e:
            print "get_file_size got error: %s" % e
            traceback.print_exc(file=sys.stdout)
            
            raise e
            
            return 0

    def download_piece(self, buffer_size, begin, end, update_callback):
        # Init.
        retries = 1
        remaining = end - begin + 1
        
        # Login.
        url = urlparse.urlparse(self.file_url)
        ftp = FTP(url[1])
        ftp.login()
        
        # Transfer data in binary mode.
        ftp.voidcmd("TYPE I")
        
        # Set offset.
        ftp.sendcmd("REST %s" % begin)
        
        # Start download.
        conn = ftp.transfercmd("RETR %s" % url[2])
        
        while True:
            if retries > 10:
                break
            
            try:
                read_size = min(buffer_size, remaining)
                if read_size <= 0:
                    break
                        
                data = conn.recv(read_size)
                if not data:
                    break
                
                remaining -= len(data)
                update_callback(begin, data)
                retries = 1
            except GreenletExit:
                # Drop received data when greenlet killed.
                break
            except Exception, e:
                print "Retries: %s(%s): %s (%s)" % (self.file_url, begin, retries, e)
                traceback.print_exc(file=sys.stdout)
                
                retries += 1
                gevent.sleep(1)
                continue
            
        # Clean work.
        conn.close()    
