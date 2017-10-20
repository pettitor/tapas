#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (c) Vito Caldaralo <vito.caldaralo@gmail.com>

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE" in the source distribution for more information.
import os, sys
from twisted.python import usage, log

class Options(usage.Options):
    optParameters = [
        ('controller', 'a', 'conventional', 'Adaptive Algorithm [conventional|tobasco|max]'),
        ('url', 'u', 'http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8', 'The playlist url. It determines the parser for the playlist'),
        ('media_engine', 'm',  'gst', 'Player type [gst|nodec|fake]'),
        ('log_sub_dir', 'l', None, 'Log sub-directory'),
        ('stress_test', 's', False, 'Enable stress test. Switch level for each segment, cyclically.'),
        ('bw_var', 'b', None, 'Set mean bandwidth and bandwidth variation (stdd) per segment comma separted in kbps, e.g. 600,60.'),
        ('min_queue_time', 'i', 1, 'Set min queue time in seconds before playback starts.')
    ]
options = Options()
try:
    options.parseOptions()
except Exception, e:
    print '%s: %s' % (sys.argv[0], e)
    print '%s: Try --help for usage details.' % (sys.argv[0])
    sys.exit(1)

def select_player():
    log.startLogging(sys.stdout)

    persistent_conn = False
    check_warning_buffering=False
    
    #MediaEngine
    if options['media_engine'] == 'gst':
        #gst_init()
        from media_engines.GstMediaEngine import GstMediaEngine
        media_engine = GstMediaEngine(decode_video=True, min_queue_time=options['min_queue_time'])
    elif options['media_engine'] == 'nodec':
        #gst_init()
        from media_engines.GstMediaEngine import GstMediaEngine
        media_engine = GstMediaEngine(decode_video=False, min_queue_time=options['min_queue_time'])
    elif options['media_engine'] == 'fake':
        from media_engines.FakeMediaEngine import FakeMediaEngine
        media_engine = FakeMediaEngine(min_queue_time=options['min_queue_time'])
    else:
        print 'Error. Unknown Media Engine'
        sys.exit()

    from twisted.internet import reactor

    #Controller
    if options['controller'] == 'conventional':
        from controllers.ConventionalController import ConventionalController
        controller = ConventionalController()
    elif options['controller'] == 'tobasco':
        from controllers.TOBASCOController import TOBASCOController
        controller = TOBASCOController()
    elif options['controller'] == 'max':
        check_warning_buffering=False
        from controllers.MaxQualityController import MaxQualityController
        controller = MaxQualityController()
    else:
        print 'Error. Unknown Control Algorithm'
        sys.exit()

    if not options['log_sub_dir']:
        log_sub_dir = options['controller']
    else:
        log_sub_dir = options['log_sub_dir'] 

    #Parser
    url_playlist = options['url']
    if ".mpd" in url_playlist:
        from parsers.DASH_mp4Parser import DASH_mp4Parser
        parser = DASH_mp4Parser(url_playlist)
    elif ".m3u8" in url_playlist:
        from parsers.HLS_mpegtsParser import HLS_mpegtsParser
        parser = HLS_mpegtsParser(url_playlist)
    else: 
        print 'Error. Unknown Parser'
        sys.exit()

    #StartPlayer
    from TapasPlayer import TapasPlayer
    player = TapasPlayer(controller=controller, parser=parser, media_engine=media_engine,
        log_sub_dir=log_sub_dir, log_period=1,
        max_buffer_time=40,
        inactive_cycle=1, initial_level=0,
        use_persistent_connection=persistent_conn,
        check_warning_buffering=check_warning_buffering,
        stress_test=options['stress_test'])

    if options['bw_var'] is not None:
        player.setBandwidthVariation(options['bw_var'])

    #print 'Ready to play'
    player.play()

    from twisted.internet import task
    def check_stop_flag():
        if player.isTerminated():
            reactor.stop()
    lc = task.LoopingCall(check_stop_flag)
    lc.start(3)
    
    try:
        reactor.run()
    except Exception, e:
        pass

if __name__ == '__main__':
    select_player()
