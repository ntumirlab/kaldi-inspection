set -e

if [ "$#" -ne 4 ]; then
    echo "usage: $0 corpus data_of_decode graph/lang decode_dir" && exit
fi

corpus=$1
data=$2
graph=$3
decode_dir=$4

# echo "$0 $1 $2 $3"
if [ -f $decode_dir/../frame_subsampling_factor ]; then
    n=`cat $decode_dir/../frame_subsampling_factor`
    frame_shift="--frame-shift 0.0$n"
fi

lmwt=`cat $decode_dir/scoring_kaldi/wer_details/lmwt`
wip=`cat $decode_dir/scoring_kaldi/wer_details/wip`
steps/get_ctm_fast.sh \
    $frame_shift --print-silence true --lmwt $lmwt --wip $wip \
    $data $graph $decode_dir $decode_dir/ctm

python word_ctm_to_mir_schema.py $data $decode_dir/ctm/ctm $decode_dir/mir

rm -rf $decode_dir/data
mkdir $decode_dir/data
for f in wav.scp text utt2spk; do
    cp $data/$f $decode_dir/data
done
if [ -f $data/segments ]; then
    cp $data/segments $decode_dir/data/segments
fi

mkdir $decode_dir/criterion_list
for criterion in cer wer; do
    if [ -f $decode_dir/scoring_kaldi/${criterion}_details/per_utt ]; then
        python gen_decode_criterion_list.py --decode_dir $decode_dir --criterion ${criterion} --save_file $decode_dir/criterion_list/${criterion}_list.txt
    fi
done

echo $corpus > $decode_dir/corpus
