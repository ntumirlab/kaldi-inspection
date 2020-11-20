from . import main
from flask import request, jsonify, redirect
from flask import send_from_directory
from flask import render_template
from ..service import kaldi


@main.route('/', methods=['GET'])
def main_portal():
    return redirect('/list', code=302)


@main.route('/list', methods=['GET'])
def showList():
    return render_template('list/index.html', decode_results=kaldi.getDecodes())


@main.route('/list/fetch', methods=['GET'])
def fetchList():
    param = {
        'decode_id': request.args.get('decode_id'),
        'criterion': request.args.get('criterion', 'wer'),
        'sort': request.args.get('sort', default='des')
    }
    if param['decode_id'] is None \
            or param['sort'] not in ['des', 'asc']\
            or param['criterion'] not in ['wer', 'cer']:
        return jsonify(
            success=False,
            message="invalid params",
            content=None
        )
    content = kaldi.fetchPerUtt(param)
    content['criterion_file'] = kaldi.fetchCriterionList(param)
    if not content:
        success = False
        message = "decode id or data does not exist"
    else:
        success = True
        message = ""
    return jsonify(
        success=success,
        message=message,
        content=content
    )


@main.route('/list/audio', methods=['GET'])
def fetchAudio():
    param = _validateDetailParam();
    if type(param) == str :
        return jsonify( success=False, message="invalid params", content=None )

    audioInfo = kaldi.fetchAudio(param)
    if not audioInfo:
        success = False
        message = "decode id or data does not exist"
    else:
        success = True
        message = ""

    return jsonify(
        success=success,
        message=message,
        content=audioInfo
    )


@main.route('/ctm/', methods=['GET'])
def ctm():
    return render_template('ctm/index.html')


def _validateDetailParam():
    decode_id = request.args.get('decode_id')
    uttid = request.args.get('uttid')
    if uttid == None:
        return "uttid is empty"
    if decode_id == None:
        return "decode_id is empty"
    return {
        'uttid': uttid,
        'decode_id': decode_id
    }


@main.route('/ctm/fetch', methods=['GET'])
def fetchCtm():
    param = _validateDetailParam()
    if type(param) == str:
        return jsonify(
            success=False,
            message=param,
            content=None
        )
    content = kaldi.fetchCtm(param)
    if not content:
        return jsonify(
            success=False,
            message="fetch utt ctm fail",
            content=None
        )

    return jsonify(
        success=True,
        message="",
        content=content
    )
