import ffmpeg
from pydub import AudioSegment
import random
import os
import time
from ttfnf import get_note_stream



#Set to a very high number for full song production
#TOTAL_DURATION = 60000
TOTAL_DURATION = 10000
#TOTAL_DURATION = 32000
SEGMENT_DURATION = 4000

SUBVIDEO_X_MAX = 1300
SUBVIDEO_Y_MAX = 500

EXTENDED_NOTE = [1,3,5]
EXTENDED_NOTE_OCTAVE = 5
EXTENDED_NOTE_DURATION = 2

BACKGROUND_IMAGE = 'input/flame_4s.mp4'

def note_to_file(octave, step_note):
    #temp change octave
    if octave < 2:
        octave = 2
    if octave > 7:
        octave = 7
    return 'input/music/' + str(octave) + '/' + str(step_note) + '.mp4'

def get_formate_notes():
    musicxml_notes = get_note_stream()
    #Limit song length on a note level (Note: might drop another part doing so)
    #musicxml_notes = get_note_stream()[:50]
    notes = []
    common_division = 80

    for note in musicxml_notes:
        is_need_extended_note = False
        new_note = {}
        if 'step' in note:
            new_note['step'] = note['step']
        if 'step_note' in note:
            new_note['step_note'] = note['step_note']
            if note['step_note'] in EXTENDED_NOTE and note['octave'] == EXTENDED_NOTE_OCTAVE:
                is_need_extended_note = True
        if 'ori_octave' in note:
            new_note['ori_octave'] = note['ori_octave']
        if 'octave' in note:
            new_note['octave'] = note['octave']
        if 'alter' in note:
            new_note['alter'] = note['alter']
        new_note['duration'] = (note['duration'] *1.1 * (EXTENDED_NOTE_DURATION if is_need_extended_note else 1) ) / float(common_division)
        new_note['start'] = note['start'] / float(common_division)
        new_note['note_strength'] = note['note_strength']

        notes.append(new_note)

    for note in notes:
        print(note)
    return notes


###########Audio part####################
def audio_process(notes, start_timestamp):
    output_audio = AudioSegment.silent(400000)# AudioSegment.from_file("g.mp4", "mp4")
    for note in notes:
        if not ('step_note' in note):
            #Slient sound
            continue
        note_file = note_to_file(note['octave'], note['step_note'])
        print(note_file)
        duration = 1000 * note['duration']
        duration = int(duration)
        start = 1000 * note['start']
        start = int(start)
        if start > TOTAL_DURATION:
            #Temp continue to test full song
            continue
        audio = AudioSegment.from_file(note_file, "mp4")
        audio = audio[:duration]
        audio = AudioSegment.silent(start) + audio
        if note['note_strength'] != 0:
            audio = audio + note['note_strength']
        output_audio = output_audio.overlay(audio)
        #Change strength:
        print('Processing Audio: Start: ',start, 'Duration:',duration)
    output_audio.export("tmp/"+start_timestamp+"/sound.wav", format="wav")
    #exit()

#############Video part################3
def video_process(notes, start_timestamp):
    all_video_path = set()
    for note in notes:
        if not ('step_note' in note):
            #Slient sound
            continue

        start = 1000 * note['start']
        start = int(start)


        if start > TOTAL_DURATION:
            #Temp continue to test full song
            continue

        segment = int(start / float(SEGMENT_DURATION))
        segment_start = int(start - segment * SEGMENT_DURATION)

        segment_video_path = "tmp/"+start_timestamp+"/video_" +str(segment).zfill(3)+ ".mp4"
        all_video_path.add(segment_video_path)
        segment_video = None
        if os.path.exists(segment_video_path):
            os.rename(segment_video_path, segment_video_path + '.old')
            segment_video = ffmpeg.input(segment_video_path + '.old')
        else:
            segment_video = ffmpeg.input(BACKGROUND_IMAGE)

        print('segment', segment, 'segment_start',segment_start, 'start', start)
        #continue
        note_file = note_to_file(note['octave'], note['step_note'])
        #clear temp mp4
        if os.path.exists("tmp/"+start_timestamp+"/tmp.mp4"):
            os.remove("tmp/"+start_timestamp+"/tmp.mp4")

        (
            ffmpeg
            .input(note_file)
            .trim(start=0, end=note['duration'])
            .output( 'tmp/'+start_timestamp+'/tmp.mp4')
            .run()
        )
        #output sliced video to temp
        #
        segment_video = ffmpeg.overlay(segment_video,
            ffmpeg.input('tmp/'+start_timestamp+'/tmp.mp4',itsoffset = segment_start/float(1000)),
            x=random.randint(1,SUBVIDEO_X_MAX),
            y=random.randint(1,SUBVIDEO_Y_MAX),
            eof_action='pass'
        )
        segment_video = ffmpeg.trim(segment_video, start=0, end=SEGMENT_DURATION / float(1000))
        segment_video = ffmpeg.output(segment_video, segment_video_path)
        ffmpeg.run(segment_video)

    #########Combine Video together###################3
    list_path = 'tmp/'+start_timestamp+'/combine_list.txt'
    combine_list = open(list_path,'a')
    all_video_path = sorted(all_video_path)
    for video_path in all_video_path:
        combine_list.write("file '../../" + video_path + "'" + '\n')
    combine_list.close()

    os.system("ffmpeg -f concat -safe 0 -i "+list_path+" -c copy tmp/"+start_timestamp+"/combine_video.mp4")

    (
        ffmpeg
        #.filter('amerge', inputs = 2['a'],)
        .output(ffmpeg.input('tmp/'+start_timestamp+'/combine_video.mp4'),
            ffmpeg.input('tmp/'+start_timestamp+'/sound.wav')['a'], 'tmp/'+start_timestamp+'/output.mp4' )
        #.output('output.mp4')
        .run()
    )
    #os.remove("tmp/sound.wav")
    #os.remove("tmp/processing_1.mp4")


############ Main Process ####################



start_timestamp = str(int(time.time()))
directory = 'tmp/'+start_timestamp
if not os.path.exists(directory):
    os.makedirs(directory)

notes = get_formate_notes()
audio_process(notes, start_timestamp)
#video_process(notes, start_timestamp)