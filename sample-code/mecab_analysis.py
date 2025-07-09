
# SageMaker Notebookインスタンスのターミナルで、まずMeCabと辞書をインストールする必要があります。
# 以下のコマンドをノートブックのセルで実行してください。
# !pip install mecab-python3 ipadic

import MeCab
import os
from collections import Counter
import re

# --- 設定 ---
# MeCabの辞書パス。`!pip install ipadic` でインストールした場合、通常は自動で解決されますが、
# 環境によっては明示的な指定が必要です。
# 例: MECAB_ARGS = "-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd"
# ここではデフォルトの辞書(ipadic)を想定します。
MECAB_ARGS = ""

# 分析対象のサンプルファイル
ABSOLUTE_FILE_PATH = "/workspaces/esio/amazon-comprehend/sample-text/sample.md"

# --- 関数定義 ---

def analyze_word_frequency_with_mecab(text):
    """
    MeCabを使ってテキストの単語出現頻度を分析する関数。
    品詞フィルタリング、原型化、ストップワード除去などのベストプラクティスを適用します。
    """
    try:
        # MeCabの初期化
        tagger = MeCab.Tagger(MECAB_ARGS)
        tagger.parse('') # UnicodeDecodeErrorを避けるためのおまじない

        print("--- MeCabによる頻出単語分析（ベストプラクティス適用） ---")
        print("品詞フィルタリング、原型化、ストップワード除去などを行い、意味のある単語を抽出します。")

        node = tagger.parseToNode(text)
        words = []
        # ストップワードの定義（カタカナの原型も追加）
        stop_words = ['こと', 'もの', 'ため', 'これ', 'それ', 'あれ', '私', 'よう', 'さん', 
                      'する', 'いる', 'なる', 'ある', 'いう', 'スル', 'イル']

        while node:
            # BOS/EOS (文頭・文末) や空のノードはスキップ
            if node.surface == "":
                node = node.next
                continue

            # 品詞情報などをカンマ区切りで取得
            features = node.feature.split(',')
            
            # エラー回避: featuresの要素数が足りない場合はスキップ
            if len(features) < 7:
                node = node.next
                continue

            pos = features[0]         # 品詞
            pos_detail1 = features[1] # 品詞細分類1
            original_form = features[6] # 原型
            surface_form = node.surface # 表層形

            # 抽出対象の品詞を定義 (名詞、動詞、形容詞、副詞)
            target_pos = ['名詞', '動詞', '形容詞', '副詞']

            if pos in target_pos:
                # 品詞によって原型を使うか表層形を使うか選択
                if pos in ['動詞', '形容詞']:
                    word_to_check = original_form
                else: # 名詞、副詞など
                    word_to_check = surface_form

                # フィルタリング処理
                is_valid = True
                # 1. 除外する品詞細分類（名詞の場合）
                if pos == '名詞' and pos_detail1 in ['非自立', '代名詞', '数', '接尾', '接続詞的']:
                    is_valid = False
                # 2. 単語が'*'や空の場合は除外
                if word_to_check == '*' or not word_to_check:
                    is_valid = False
                # 3. ストップワードに含まれていれば除外
                if word_to_check in stop_words:
                    is_valid = False
                # 4. 1文字のひらがな・カタカナは除外 (漢字やアルファベットは残す)
                if len(word_to_check) == 1 and re.fullmatch(r'[ぁ-んァ-ヶ]', word_to_check):
                    is_valid = False

                if is_valid:
                    words.append(word_to_check)
            
            node = node.next
        
        word_counts = Counter(words)
        print("\n最も頻繁に出現する意味のある単語 (トップ15):")
        if word_counts:
            for word, count in word_counts.most_common(15):
                print(f"- {word}: {count}回")
        else:
            print("分析対象の単語が見つかりませんでした。")

    except RuntimeError as e:
        print(f"MeCabの実行エラー: {e}")
        print("MeCabまたは辞書が正しくインストールされていない可能性があります。")
        print("ノートブックのセルで `!pip install mecab-python3 ipadic` を実行してください。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

# --- メイン処理 ---

if __name__ == '__main__':
    try:
        with open(ABSOLUTE_FILE_PATH, 'r', encoding='utf-8') as f:
            sample_text = f.read()
        
        analyze_word_frequency_with_mecab(sample_text)

    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません。パスを確認してください: {ABSOLUTE_FILE_PATH}")
    except Exception as e:
        print(f"メイン処理でエラーが発生しました: {e}")
