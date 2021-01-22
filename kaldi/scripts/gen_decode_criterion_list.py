import os
import sys
import csv
import re
import argparse
from argparse import ArgumentParser, RawTextHelpFormatter

def setArgument() :
    parser = ArgumentParser(
        description='Pass a decode dir. with scoring, data dir, and scoring criterion, \n'+
                    'this program will make a file include the decode info of each utterence and sort in desc. order by error rate.\n'+
                    'Example: python gen_decode_criterion.py --decode_dir exp/chain/decode_text --data data/test --criterion cer --save_file cer_info.txt',
        formatter_class=RawTextHelpFormatter)
    parser.add_argument("-de", "--decode_dir", default="", type=str, dest = "decode_dir", help = "Pass in a decoded dir")
    parser.add_argument("-c", "--criterion", default="cer", type=str, dest = "criterion", choices=['cer', 'wer'], help = "Pass in a criterion type.")
    parser.add_argument("-da", "--data", default="", type=str, dest="data", help = "Pass in a data dir, it default to $decode_set/data.")
    parser.add_argument("-q", "--quantity", default=None, type=int, dest="quantity", help = "Pass in a integer that how many data need to save, it default to save all data.")
    # save Path
    parser.add_argument("-s", "--save_file", default="", type=str, dest = "save_file", help = "Pass in a file, it default to ${criterion}_info.txt.")
    args = parser.parse_args()
    return args

# check folder path exist
def checkPath( folder ): 
    if os.path.isdir( folder ) :
        return True ;
    else :
        return False ;
    return False ;    

# check file exist
def checkFile( file ): 
    if os.path.isfile( file ) :
        return True ;
    else :
        return False ;
    return False ;

# remove mulit space in text
def removeMulitSpace( text ) :
    spaceRE = re.compile( r"[ ]+" )
    new_text = spaceRE.sub( ' ' , text )
    return new_text

# calculator wer/cer
def criterionErrorRate( csidList ) :
    c = int(csidList[0])
    s = int(csidList[1])
    i = int(csidList[2])
    d = int(csidList[3])
    
    errorRate = -1
    if c + s + d > 0 :
        errorRate = ( s + i + d ) / ( c + s + d )
    else :  # empty reference but non-empty decode result
        errorRate = i
    return errorRate

# get audio path position in a list split of space from wav.scp
def getAudioPosInScp(line):
    tokens = line.split()
    if len(tokens) == 2:
        return 1
    # assuming ext naming are 3 chars len or is flac file :(
    for i, token in enumerate(tokens):
        if (len(token) > 4 and token[-4] == '.') or (len(token) > 5 and token.endswith(".flac")) :
            return i
    return -1

# read scoring per_utt file
def readPeruttFile( per_utt ) :
    uttDict = {}
    
    # read per_utt file
    f = open( per_utt , 'r' , encoding='utf8' )
    for line in f :
        # get ref, hyp, csid
        ref = removeMulitSpace( line ).strip().split(' ')
        hyp = removeMulitSpace( next(f) ).strip().split(' ')
        ops = removeMulitSpace( next(f) ).strip().split(' ')
        csid = removeMulitSpace( next(f) ).strip().split(' ')
        if ref[0] != hyp[0] or hyp[0] != ops[0] or ops[0] != csid[0] :
            raise Exception("reading per_utt Error : data not match.")
        
        uttid = ref[0]
        errorRate = criterionErrorRate( csid[2:] ) # get criterion error rate
        uttDict[ uttid ] = {"uttid": uttid, "ref": ref[2:], "hyp": hyp[2:], "ops": ops[2:], "csid": csid[2:], "cer": errorRate}
    f.close()
    
    return uttDict ;

# read segments
def readSegmentsFile( segments ) :
    segmentDict = {}
    
    # read segments file
    f = open( segments , 'r' , encoding='utf8' )
    for line in f :
        info = removeMulitSpace( line ).strip().split(' ')
        uttid = info[0]
        segmentDict[ uttid ] = {"wavid": info[1], "start":info[2], "end":info[3]}
    f.close()
    
    return segmentDict ;

# read wav.scp
def readWavscpFile( wav_scp ) :
    wavDict = {}
    
    wav_position = -1 
    # read per_utt file
    f = open( wav_scp , 'r' , encoding='utf8' )
    # read first line to find wav file position
    fline = removeMulitSpace( next(f) ).strip()
    info = fline.split(' ')
    uttid = info[0]
    wav_position = getAudioPosInScp( fline )
    wavDict[ uttid ] = {"wavPath": info[wav_position]}
    # read other line base on the wav position we finded
    for line in f :
        info = removeMulitSpace( line ).strip().split(' ')
        uttid = info[0]
        wavDict[ uttid ] = {"wavPath": info[wav_position]}
    f.close()
    
    return wavDict ;

# get the wav file path from wavDict and interval from segmentsDict if exist, merge all info to uttDict & convert to a sort list
def mergeDecodeInfo( peruttDict, wavDict, segmentDict = None ) :
    if segmentDict :
        for uttid in peruttDict :
            startTime = segmentDict[uttid]["start"]
            endTime = segmentDict[uttid]["end"]
            wavid = segmentDict[uttid]["wavid"]
            wavPath = wavDict[wavid]["wavPath"]
            peruttDict[uttid]["start"] = startTime
            peruttDict[uttid]["end"] = endTime
            peruttDict[uttid]["wavPath"] = wavPath
            peruttDict[uttid]["segments"] = True
    else :
        for uttid in peruttDict :
            wavPath = wavDict[uttid]["wavPath"]
            peruttDict[uttid]["wavPath"] = wavPath
            peruttDict[uttid]["segments"] = False
    return peruttDict ;

# save decode info to a file
def savePeruttDict( perUttList , criterion , save_file ) :
    f = open( save_file , 'w' , encoding="utf8" )
    for utt_info in perUttList :
        uttid = utt_info["uttid"]
        f.write( uttid + "\n" )
        f.write( "wav_file " + utt_info["wavPath"] + "\n" )
        f.write( criterion + " " + format(utt_info["cer"], ".4f") + "\n" )
        f.write( "csid " + ' '.join(utt_info["csid"]) + "\n" )
        f.write( "ops " + ' '.join(utt_info["ops"]) + "\n" )
        f.write( "ref " + ' '.join(utt_info["ref"]) + "\n" )
        f.write( "hyp " + ' '.join(utt_info["hyp"]) + "\n" )
        if utt_info["segments"] :
            f.write( "interval " + utt_info["start"] +"," + utt_info["end"] + "\n" )
    f.close()
    return ;

if __name__ == "__main__" :  
    # set Argument
    args = setArgument()
    
    self = sys.argv[0]
    runDir , self = os.path.split(os.path.realpath(self))
    # read argument
    decode_dir = args.decode_dir
    data_dir = args.data
    criterion = args.criterion.lower()
    quantity = args.quantity
    save_file = args.save_file
    # check argument
    if not checkPath( decode_dir ) :
        raise argparse.ArgumentTypeError('decode_dir not exists : '+decode_dir)
    if not data_dir or data_dir == "" :
        data_dir = os.path.join( decode_dir , "data" )
    if not checkPath( data_dir ) :
        raise argparse.ArgumentTypeError('data_dir not exists : '+data_dir)
    save_path = os.path.dirname( save_file )
    if save_file == "" :
        save_file = criterion+"_info.txt"
    if save_path != '' and not checkPath( save_path ) :
        print('save_path:' + save_path + ' not exists, create it automatically.')
        os.makedirs( save_path )
    elif checkFile( save_file ) :
        print('save_file:' + save_file + ' exists, remove it automatically.')
        os.remove( save_file )
    
    # read per_utt
    scoring_dir = os.path.join( decode_dir , "scoring_kaldi/"+criterion+"_details" )
    per_utt_file = os.path.join( scoring_dir , "per_utt" )
    if not checkFile( per_utt_file ) :
        raise Exception('per_utt not exists in '+per_utt_file)
    peruttDict = readPeruttFile( per_utt_file )
    
    # read segments if exist
    segments_file = os.path.join( data_dir , "segments" )
    segmentDict = None ;
    if checkFile( segments_file ) :
        segmentDict = readSegmentsFile( segments_file )
        
    # read wav.scp
    wav_scp_file = os.path.join( data_dir , "wav.scp" )
    if not checkFile( wav_scp_file ) :
        raise Exception('wav.scp not exists in '+wav_scp_file)
    wavDict = readWavscpFile( wav_scp_file )
    
    # merge all info to a 2D-list
    mergeDecodeInfo( peruttDict, wavDict, segmentDict )
    
    # convert to a list & sort by cer in desc.
    perUttList = list( peruttDict.values() )
    perUttList = sorted(perUttList, key=lambda item: item['cer'], reverse=True) 
    
    #save file
    if quantity :
        perUttList = perUttList[:quantity]
    savePeruttDict( perUttList , criterion , save_file )
    print("Done!!")
