# -*- coding: UTF-8 -*-
from flask import current_app as app
import os
import sys
import json

# get audio path position in a list split of space from wav.scp
def _getAudioPosInScp(line0):
    tokens = line0.split()
    if len(tokens) == 2:
        return 1
    # assuming ext naming are 3 chars len :(
    for i, token in enumerate(tokens):
        if len(token) > 4 and token[-4] == '.':
            return i
    return -1

def _checkConsistency(content):
    if len(content['utts']) != len(content['wav']):
        return False
    for utt in content['utts']:
        if utt not in content['wav']:
            return False
    for utt in content['wav']:
        if utt not in content['utts']:
            return False
    return True

# calculate utts wer by csid
def _getWer(csid):
    errs = float(csid[1]) + float(csid[2]) + float(csid[3])
    occs = float(csid[0]) + float(csid[1]) + float(csid[3])
    if occs == 0.0:
        return errs
    return errs/occs

# get dateset corpus name from decode_dir
def _getCorpusName(decode_dir):
    # get corpus name
    corpus_file = decode_dir+"/corpus"
    with open(corpus_file, "r", encoding="utf-8") as fp:
        lines = fp.read().splitlines()
    if len(lines) != 1:
        return None ;
    return lines[0] ;

# get the wav path use of website page & segments times of wav
def _getAudioInfo(uttid, decode_dir):
    # get corpus name
    corpus = _getCorpusName( decode_dir )
    if not corpus:
        return {"error": "corpus file no data!"}

    # get wav path
    wavscp = decode_dir + "/data/wav.scp"
    if not os.path.exists(wavscp):
        return {"error": "data wav.scp not exist!"}
    with open(wavscp, "r", encoding="utf-8") as fp:
        lines = fp.read().splitlines()
    if len(lines) == 0:
        return {'error': "read wav.scp error!"}

    # find audio position in wav.scp
    tokens = lines[0].split()
    audio_file_pos = _getAudioPosInScp(lines[0])
    if audio_file_pos < 1:
        return {'error':"audio_file_pos < 1!"}

    # get wav id if segments exist
    segments = decode_dir + "/data/segments"
    segmentsTimes = None
    if os.path.exists( segments ):
        with open(segments, "r", encoding="utf-8") as fp :
            for segment in fp.read().splitlines() :
                tokens = segment.split()
                if tokens[0] == uttid:
                    uttid = tokens[1]
                    segmentsTimes = [tokens[2], tokens[3]]
                    break;

    # find wav of given utt in wav.scp
    wav_relative_path = ""
    for line in lines:
        tokens = line.split()
        if tokens[0] == uttid:
            wav_tokens = tokens[audio_file_pos].split(corpus+"/")
            if len(wav_tokens) != 2:
                return {'error':"wav token error!!! Corpus: "+corpus+", File_pos: "+str(audio_file_pos)+", Wav_tokens: ["+",".join(tokens)+"]"}
            wav_relative_path = "/static/dataset/" + \
                corpus + "/" + wav_tokens[1]

    # utt not found
    if wav_relative_path == "":
        return {'error':"utt not found in wav.scp! uttid: "+uttid}

    audioInfo = {'wav': wav_relative_path, 'segments': segmentsTimes}
    return audioInfo ;

# get sorted utterences decode result
def fetchCriterionList(param):
    decode_dir = param['decode_id']
    decode_folder = app.config['DECODES_FOLDER']

    static_folder = os.path.join("./static/result", decode_dir)
    static_list_file = os.path.join(static_folder, param['criterion']+"_list.txt")
    if not os.path.exists( static_list_file ) :
        origin_list_file = os.path.join(decode_folder, decode_dir, "criterion_list", param['criterion']+"_list.txt")
        if not os.path.exists( origin_list_file ) :
            return ""
        if not os.path.exists( static_folder ) :
            os.makedirs( static_folder )
        os.symlink(origin_list_file, static_list_file)
    return static_list_file

# get utterences info. as a list
def fetchPerUtt(param):
    try :
        content = {'utts': {}}
        decode_dir = param['decode_id']
        if decode_dir in os.listdir(app.config['DECODES_FOLDER']):
            scoring_dir = app.config['DECODES_FOLDER'] + "/" + decode_dir + \
                '/scoring_kaldi/'

            print( scoring_dir + param['criterion'] + '_details' )
            if not os.path.exists(scoring_dir + param['criterion'] + '_details'):
                return {"error": "criterion details not exist!"}
            per_utt = scoring_dir + param['criterion'] + '_details' + '/per_utt'

            # read per utt
            count = 0
            with open(per_utt, "r", encoding="utf-8") as fp:
                lines = fp.read().splitlines()
            for line in lines:
                tokens = line.replace("<","&#60;").replace(">","&#62;").split()
                if count == 0:
                    content['utts'][tokens[0]] = {}
                if count == 3:
                    content['utts'][tokens[0]]["csid"] = tokens[2:]
                    content['utts'][tokens[0]]['wer'] = _getWer(tokens[2:])
                    content['utts'][tokens[0]]['ctm_link'] = "/ctm/?decode_id=" + \
                        param['decode_id']+"&uttid="+tokens[0]
                    count = -1
                else:
                    content['utts'][tokens[0]][tokens[1]] = tokens[2:]
                count += 1

            # read overall wer
            wer_file = scoring_dir + "/best_" + param['criterion'].lower()
            if not os.path.exists(wer_file):
                return {"error": "wer file not exist!"}
            with open(wer_file, "r", encoding="utf-8") as fp:
                lines = fp.read().splitlines()
            tokens = lines[0].split()
            content['wer'] = tokens[1]

        else:
            return {"error": "decode_dir not exist!"}

    except Exception as e :
        return {"error": "fetchPerUtt Error: " + str(e)}
    return content

# get utterences ctm & audio info as a dict
def fetchCtm(param):
    try :
        uttid = param["uttid"]
        # get mir ctm
        expdir = app.config['DECODES_FOLDER']
        decode_dir = expdir+"/"+param['decode_id']
        mir_ctm_file = decode_dir + "/mir/"+param['uttid']+'.json'
        if not os.path.exists(mir_ctm_file):
            return {"error": "ctm json file not exist!"}
        with open(mir_ctm_file , "r", encoding="utf-8") as fp:
            ctm = json.load(fp)

        audioInfo = _getAudioInfo(uttid , decode_dir) ;
        if "error" in audioInfo :
            return {"error": audioInfo["error"]}

        return {
            'ctm': ctm,
            'audio': audioInfo
        }
    except Exception as e :
        return {"error": "fetchCtm Error: " + str(e)}

# get utterences audio info as a dict
def fetchAudio(param):
    uttid = param["uttid"]
    expdir = app.config['DECODES_FOLDER']
    decode_dir = expdir+"/"+param['decode_id']

    audioInfo = _getAudioInfo(uttid , decode_dir) ;
    if "error" in audioInfo :
        return {"error": audioInfo["error"]}

    return audioInfo ;

def getDecodes():
    return sorted([d for d in os.listdir(app.config['DECODES_FOLDER'])
            if os.path.islink(app.config['DECODES_FOLDER']+"/"+d)
            or os.path.isdir(app.config['DECODES_FOLDER']+"/"+d)])
