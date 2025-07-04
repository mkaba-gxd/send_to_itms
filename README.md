# send_to_itms ツール
iTMSへ送付するデータのシンボリックリンクとチェックサムを作成する。
## 送付データ
### **eWES**
<img src="https://github.com/user-attachments/assets/cd1eb924-470a-4087-b647-d831edc29c51" width="1000">

### **WTS**
<img src="https://github.com/user-attachments/assets/67533440-aa2c-4a35-8c6f-3020910bd0f6" width="1000"> \
※ 転送するデータが1つでも足りない場合、当該検体のリンク作成とチェックサムの作成は行わない
## エイリアスの作成（初回のみ）
~/bin フォルダを作成し、以下のコマンドを記載したテキストファイル send_to_itms を作成し、実行権限を付与する。
（エイリアスを作成しない場合は、singularity でコンテナを指定して実行する）
```
singularity exec --disable-cache --bind /data1 /data1/labTools/labTools.sif python /data1/labTools/send_to_itms/latest/send_to_itms.py $@
```
usage を表示してエイリアスの設定を確認する。以下が表示されればOK。
```
$ send_to_itms --help
version: v2.1.0
usage: send_to_itms.py [-h] [--listfile LISTFILE] [--sample SAMPLE] [--directory DIRECTORY]
                   [--transfer TRANSFER] [--version]

Data Creation Tool for iTMS Sending.

optional arguments:
  -h, --help            show this help message and exit
  --listfile LISTFILE, -f LISTFILE
                        List of samples to be transferred. (default: None)
  --sample SAMPLE, -s SAMPLE
                        sample ID (default: None)
  --directory DIRECTORY, -d DIRECTORY
                        parent analytical directory (default: /data1/data/result)
  --transfer TRANSFER, -t TRANSFER
                        working directory (default: /data1/work/send_to_ITMS)
  --version, -v         show program's version number and exit
```
## 実行方法
--listfile でリストファイルを指定、または --sampleでSampleIDをコンマ区切りで指定する。
```
send_to_itms --listfile <送付するサンプルリストファイルパス>
send_to_itms --sample <送付するサンプルID>
```
| option        |required | 概要                                         |default            |
|:--------------|:-------:|:---------------------------------------------|:------------------|
|--listfile/-f  |False*   |転送する検体のSample IDリストのファイルパス。<br> Sample IDを1列に記載する |None |
|--sample/-s    |False*   |転送する検体のSample ID（タブ区切りで複数指定可）|None               |
|--directory/-d |False    |解析フォルダの親ディレクトリ                    |/data1/data/result |
|--transfer/-t  |False    |転送用のデータセット出力先                      |/data1/work/send_to_ITMS |

**\*--listfile または --sample のいずれか1つを指定すること**\
検査種別は混合していても問題ないが、M3検体かどうかの判別は行わないため、\<TRANSFER\>/\<timestamp\>.idx で不要な検体が含まれていないかを確認する。

指定された Sample ID の解析データのうち、**データベースで最新**のもの（gc_history_logのidxが最大値）を検索して以下の挙動を示す。
- \<TRANSFER\>/\<timestamp\>/GxD に既定のディレクトリ構造でシンボリックリンクを作成する。
- \<TRANSFER\>/\<timestamp\>/checksum.txt に各ファイルのチェックサムを書き出すジョブを投入する。
- \<TRANSFER\>/\<timestamp\>.idx に送付準備ができた batch, Sample ID, Customer Sample ID の一覧を作成する。

⇒ 全ての検体に対してジョブが投入されたら、rsync -avLzu コマンドで解析データを送付用HDDへ転送する。\
（データ転送には時間がかかるので、nohupでのバックグラウンド実行を推奨）\
⇒ すべてのジョブが完了したら、\<TRANSFER\>/\<timestamp\>/checksum.txt の /media/usb/cap/checksum.txt への追記を実施する。
