# MIR kaldi inspection tool

## Introduction

把 prebuilt 好的 kaldi recipe （或基於 kaldi standard recipe 建立的 egs），將一個 decode 結果的 ctm （透過 `steps/get_ctm_fast.sh` 取得）render 成 html。

![Image of demo listing](https://github.com/kakushawn/kaldi-inspection/blob/develop/list-demo.png)
![Image of demo listing](https://github.com/kakushawn/kaldi-inspection/blob/develop/ctm-demo.png)


## Build steps

### 1. start server

1. `git clone https://github.com/kakushawn/kaldi-inspection`

2. `cd kaldi-inspection`

3. `pip install -r requirements.txt`

4. 修改 `config.py`，把 ROOT_FOLDER 改成對應路徑。

5. 執行 `python run.py` 啟動 server，應該可以連到 localhost:5000

### 2. linking kaldi dependencies

1. 將語料建立軟連結到 static/dataset/ 下。

    `ln -s ~/kaldi-asr/egs/yesno/s5/waves_yesno static/dataset/`

2. 將 kaldi/scripts 腳本複製到 kaldi 腳本目錄下。

    `cp kaldi/scripts/* ~/kaldi-asr/egs/aishell/s5/`

3. 在 kaldi 腳本目錄下，執行 `gen_mir_web_ana_data.sh`，把 decode 結果產生網站需要的文件。
  * usage:

    `gen_mir_web_ana_data.sh corpus data_of_decode graph/lang decode_dir`

    * corpus: 語料目錄名稱
    * data_of_decode: 該次 decode 執行時的 data 目錄
    * graph/lang: 該次 decode 時用到的 graph 或 lang 目錄
    * decode_dir: decode 完的目錄

    * example:

      ```
      cd ~/kaldi-asr/egs/yesno/s5/
      ./gen_mir_web_ana_data.sh waves_yesno data/test_yesno data/lang_test_tg exp/mono0a/decode_test_yesno/
      ```

4. 回到網站目錄，在 kaldi/decodes/ 建立 decode 目錄的軟連結。

    `ln -s ~/kaldi-asr/egs/yesno/s5/exp/mono0a/decode_test_yesno/ kaldi/decodes/`

5. 打開首頁，選項應該有剛剛新增的 decode 目錄。若要再新增其他目錄重複步驟 3 到 4 即可。

## Notes

1. 目前針對取得 audio resource 的方法非常 workaround，需要 flask server 與 corpus 在同一個 server，且只針對 wav 檔處理。

## Todo

1. 列表頁重新排版
2. kaldi.py code整理，fetchPerUtt & fetchCriterionList應該可簡化
