import subprocess
import re

option_func = {
    'from-option-file': lambda filename: [u"@%s" % filename],
    'global': {
            'attachment': {
                    'attachment-description': lambda desc: [u"--attachment-description", u"%s" % desc], 
                    'attachment-mime-type': lambda type: [u"--attachment-mime-type", u"%s" % type],
                    'attachment-name': lambda name: [u"--attachment-name", u"%s" % name],
                    'attach-file': lambda filename, once=False: [u"--attach-file%s" % ("-once" if once else ""), u"%s" % filename],
                },
            'chapters': {
                    'chapter-charset': lambda charset: [u"--chapter-charset", u"%s" % charset],
                    'chapter-language': lambda lang: [u"--chapter-language", u"%s" % lang],
                    'chapters': lambda filename: [u"--chapters", u"%s" % filename],
                    'cue-chapter-name-format': lambda format: [u"--cue-chapter-name-format", u"%s" % format],
                },
            'cluster-length': lambda spec: [u"--cluster-length", u"%s" % spec],
            'clusters-in-meta-seek': lambda: [u"--clusters-in-meta-seek"],
            'default-language': lambda lang: [u"--default-language", u"%s" % lang],
            'disable-lacing': lambda: [u"--disable-lacing"],
            'enable-duration': lambda: [u"--enable-duration"],
            'global-tags': lambda filename: [u"--global-tags", u"%s" % filename],
            'identify': lambda filename, verbose=False: [u"--identify%s" % ("-verbose" if verbose else ""), u"%s" % filename],
            'linear': {
                    '=': lambda file: [u"=%s" % file],
                    'append': lambda file: [u"+%s" % file],
                    'append-mode': lambda mode: [u"--append-mode", u"%s" % mode],
                    'append-to': lambda *args: \
                            [u"--append-to", u"%s" % ','.join('%d:%d:%d:%d' % (st.file.id, st.id, dt.file.id, dt.id) for st, dt in args)],
                    'concat': lambda *files: [u"'('" + [u"%s" % f for f in files] +  u"')'"],
                    'link': lambda: ["--link"],
                    'link-to-next': lambda sid: [u"--link-to-next", u"%s" % sid],
                    'link-to-previous': lambda sid: [u"--link-to-previous", u"%s" % sid],
                },
            'no-cues': lambda: [u"--no-cues"],
            'output': lambda filename: [u"-o", u"%s" % filename],
            'priority': lambda priority: [u"--priority", u"%s" % priority],
            'quite': lambda: [u"-q"],
            'segmentinfo': {
                    'segmentinfo': lambda filename: [u"--segmentinfo", u"%s" % filename],
                    'segment-uid': lambda *args: \
                            [u"--segment-uid", u"%s" % ','.join(str(a) for a in args)],
                },
            'split': lambda spec: [u"--split", u"%s" % spec], 
            'timecode-scale': lambda factor: [u"--timecode-scale", u"%s" % factor],
            'title': lambda title: [u"--title", u"%s" % title],
            'track-order': lambda *args: \
                    [u"--track-order", u"%s" % ','.join('%d:%d' % (track.file.id, track.id) for track in args)],
            'verbose': lambda: [u"-v"],
            'ui-language': lambda lang: [u"--ui-language", u"%s" % lang],
            'webm': lambda: [u"-w"],
        },
    'files': {
            'aac-is-sbr': lambda t, bool=True: [u"--aac-is-sbr", u"%d%s" % (t.id, ":0" if not bool else "")],
            'attachments': lambda *tracks: [u"-m", u"%s" % \
                    ','.join("%s%d:%s" % ("!" if t.no else "", t['track'].id, t['mode'] \
                                if isinstance(t, dict) else t.id) for t in tracks)],
            'audio-tracks': lambda *tracks: [u"-a", u"%s" % \
                    ','.join("%s%d" % ("!" if t.no else "", t.id) for t in tracks)],
            'blockadd': lambda t, level: [u"--blockadd", u"%d:%d" % (t.id, level)],
            'button-tracks': lambda *tracks: [u"-b", u"%s" % \
                    ','.join("%s%d" % ("!" if t.no else "", t.id) for t in tracks)],
            'compression': lambda t, n: [u"--compression", u"%d:%s" % (t.id, n)],
            'cues': lambda t, mode: [u"-y", u"%d:%s" % (t.id, mode)],
            'default-duration': lambda t, x: [u"--default-duration", u"%d:%s" % (t.id, x)],
            'default-track': lambda t, bool=True: [u"--default-track", u"%d%s" % (t.id, ":0" if not bool else "")],
            'forced-track': lambda t, bool=True: [u"--forced-track", u"%d%s" % (t.id, ":0" if not bool else "")],
            'language': lambda t, lang: [u"--language", u"'n%d:%s'" % (t.id, lang)],
            'nalu-size-length': lambda t, n: [u"--nalu-size-length", u"%d:%d" % (t.id, n)],
            'no-attachment': lambda: [u"-M"],
            'no-audio': lambda: [u"-A"],
            'no-buttons': lambda: [u"-B"],
            'no-chapters': lambda: [u"--no-chapters"],
            'no-global-tags': lambda: [u"--no-global-tags"],
            'no-subtitles': lambda: [u"-S"],
            'no-track-tags': lambda: [u"-T"],
            'no-video': lambda: [u"-V"],
            'sync': lambda t, d, o=1, p=1: [u"-y", u"%d:%d,%f/%f" % (t.id, d, o, p)],
            'subtitles': {
                    'sub-charset': lambda t, charset: [u"--sub-charset", u"%d:%s" % (t.id, charset)],
                },
            'subtitle-tracks': lambda *tracks: [u"-s", u"%s" % \
                    ','.join("%s%d" % ("!" if t.no else "", t.id) for t in tracks)],
            'video': {
                    'aspect-ratio': lambda ratio=None, width=None, height=None: \
                            [u"--aspect-ratio", u"%d:%f" % (t.id, ratio) if ratio != None else \
                                                u"%d:%d/%d" % (t.id, width, height)],
                    'aspect-ratio-factor': lambda factor=None, n=None, d=None: \
                            [u"--aspect-ratio-factor", u"%d:%f" % (t.id, factor) if factor != None else \
                                                       u"%d:%f/%f" % (t.id, n, d)],
                    'cropping': lambda t, left=0, top=0, right=0, bottom=0: \
                            [u"--cropping", u"%d:%d,%d,%d,%d" % (t.id, left, top, right, bottom)],
                    'display-dimensions': lambda t, width, height: [u"--display-dimensions", u"%d:%dx%d" % (t.id, width, height)],
                    'fourcc': lambda t, fourcc: [u"-f", u"%d:%s" % (t.id, fourcc)],
                    'stereo-mode': lambda t, mode: [u"--stereo-mode", u"%d:%s" % (t.id, mode)],
                },
            'video-tracks': lambda *tracks: [u"-d", u"%s" % \
                    ','.join("%s%d" % ("!" if t.no else "", t.id) for t in tracks)],
            'tags': lambda t, filename: [u"-t", u"%d:%s" % (t.id, filename)],
            'timecodes': lambda t, filename: [u"--timecodes", u"%d:%s" % (t.id, filename)],
            'track-name': lambda t, name: [u"--track-name", u"%d:%s" % (t.id, name)],
            'track-tags': lambda *tracks: [u"--track-tags", u"%s" % \
                    ','.join("%s%d" % ("!" if t.no else "", t.id) for t in tracks)],
        }
    }

default_options = []

def set_default_options(options):
    global default_options
    default_options = options

class File(object):
    def __init__(self, name, id=None):
        self.name = name
        self.id = id
        self.sid = None
        self.audio_tracks = []
        self.button_tracks = []
        self.subtitle_tracks = []
        self.video_tracks = []

    def __unicode__(self):
        return unicode(self.name)
    
    def __str__(self):
        return self.name

    @staticmethod
    def get_object(file):
        if isinstance(file, File):
            return file
        else:
            return File(file)

class Track(object):
    def __init__(self, file, id, no=False):
        self.file = file
        self.id = id
        self.no = no

    def __unicode__(self):
        return u"%s [%d]" % (self.name, self.id)
    
    def __str__(self):
        return str(unicode(self))

    def __neg__(self):
        return type(self)(file=self.file, id=self.id, no=not self.no)

    def __invert__(self):
        return -self

class AudioTrack(Track):
    def __unicode__(self):
        return u"%s audio" % super(AudioTrack, self).__unicode__()

class ButtonTrack(Track):
    def __unicode__(self):
        return u"%s button" % super(ButtonTrack, self).__unicode__()

class VideoTrack(Track):
    def __unicode__(self):
        return u"%s video" % super(VideoTrack, self).__unicode__()

class SubtitleTrack(Track):
    def __unicode__(self):
        return u"%s subtitles" % super(SubtitleTrack, self).__unicode__()

class MKVMerge(object):
    def __init__(self, output, *input_filenames):
        self.output = output
        self.input_files = []
        for id, file in enumerate(input_filenames):
            if isinstance(file, File):
                f = file
                f.id
            else:
                f = File(file, id)
            self.input_files.append(f)
    
    @staticmethod
    def run(options):
        args = [u"mkvmerge"] 
        args.extend(options)
        args.extend(default_options)
        print args
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        return p.returncode, p.stdout.readlines(), p.stderr.readlines()

    @staticmethod 
    def identify(file, verbose=False):
        file = File.get_object(file)
        options = option_func['global']['identify'](file, verbose)
        errno, stdout, stderr = MKVMerge.run(options)
        if errno != 0:
            raise Exception((errno, stdout, stderr))
        streaminfo = []
        for streaminfo_str in stdout[1:-2]:
            match = re.match(r"Track ID (?P<id>[0-9]+): (?P<type>[a-z]+) \((?P<codec_id>.+)\) \[(?P<verbose_info>.+)\]\n", streaminfo_str)
            if match:
                g = match.group
                si = {
                        'id': int(g('id')),
                        'type': g('type'),
                        'codec_id': g('codec_id'),
                    }
                for v in g('verbose_info').split():
                    key, value = v.split(':')
                    if value.isdigit():
                        value = int(value)
                    si[key] = value
                streaminfo.append(si)
        return streaminfo


    def split(self, *args, **kwargs):
        spec = ''
        # TODO
        option_func['global']['split'](spec)
    
    def get_input_files(self):
        return dict(enumerate(self.input_files))

