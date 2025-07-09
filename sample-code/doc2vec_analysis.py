# ライブラリのバージョン非互換エラーを解消するため、以下の手順でライブラリを再インストールしてください。
# 1. 以下のコマンドを実行し、古いバージョンのgensimをアンインストールします。
# !pip uninstall -y gensim

# 2. 続けて以下のコマンドを実行し、ライブラリをインストールします。
# !pip install gensim mecab-python3 ipadic

# 3. 上記2つのコマンドを実行した後、Jupyterメニューの「Kernel」>「Restart Kernel」を選択してカーネルを再起動してください。

import os
import glob
import MeCab
from gensim.models.doc2vec import Doc2Vec, TaggedDocument

import re

# --- 設定 ---
MECAB_ARGS = ""
# サンプル文書が格納されているディレクトリ
SAMPLE_DIR_PATH = "/workspaces/esio/amazon-comprehend/sample-text/"

# --- 関数定義 ---

def preprocess_text_for_doc2vec(text):
    """
    doc2vecの学習用にテキストを前処理（わかち書きとフィルタリング）する関数。
    ルールベースで不要な単語を除去する根本対策を適用。
    """
    tagger = MeCab.Tagger(MECAB_ARGS)
    tagger.parse('')
    node = tagger.parseToNode(text)
    
    words = []
    # 名詞などの基本的なストップワード
    stop_words = ['こと', 'もの', 'ため', 'これ', 'それ', 'あれ', '私', 'よう', 'さん']

    while node:
        if not node.surface:
            node = node.next
            continue

        features = node.feature.split(',')
        if len(features) < 7:
            node = node.next
            continue

        pos = features[0]
        pos_detail1 = features[1]
        original_form = features[6]
        surface_form = node.surface

        target_pos = ['名詞', '動詞', '形容詞', '副詞']
        if pos in target_pos:
            word_to_check = original_form if pos in ['動詞', '形容詞'] else surface_form

            # --- フィルタリングルール ---
            # 1. 単語が'*'や空の場合は除外
            if word_to_check == '*' or not word_to_check:
                continue
            # 2. 基本的なストップワード（主に名詞）を除外
            if word_to_check in stop_words:
                continue
            # 3. 特定の品詞（助数詞など）を除外
            if pos == '名詞' and pos_detail1 in ['数', '非自立', '代名詞', '接尾']:
                continue
            # 4. 【根本対策】動詞・形容詞で、原型がすべてカタカナのものは除外
            if pos in ['動詞', '形容詞'] and re.fullmatch(r'[ァ-ヶー]+', word_to_check):
                continue
            
            words.append(word_to_check)

        node = node.next
    return words

def analyze_with_doc2vec(documents):
    """
    Doc2Vecモデルを学習し、分析例を実行する関数。
    """
    try:
        print("--- Doc2Vecモデルの学習 ---")
        tagged_documents = [TaggedDocument(doc, [f'doc_{i}']) for i, doc in enumerate(documents)]
        
        # min_count=2のままでも、データ量を増やしたことで多くの単語が学習対象になる
        # workersパラメータを追加して、CPUコアを最大限活用し処理を高速化
        model = Doc2Vec(vector_size=100, min_count=2, epochs=40, workers=os.cpu_count())
        model.build_vocab(tagged_documents)
        
        print(f"モデルの学習を開始します... (対象文書: {len(documents)}件)")
        model.train(tagged_documents, total_examples=model.corpus_count, epochs=model.epochs)
        print("モデルの学習が完了しました。")
        
        print("\n" + "="*50 + "\n")

        print("--- Doc2Vecによる分析例：類似単語の検索 ---")
        
        search_words = ['製品', '機能', 'イヤホン', '翻訳']
        for word in search_words:
            print(f"\n単語 '{word}' に意味が近い単語トップ5:")
            try:
                similar_words = model.wv.most_similar(word, topn=5)
                for sim_word, similarity in similar_words:
                    print(f"- {sim_word} (類似度: {similarity:.4f})")
            except KeyError:
                print(f"'{word}' は語彙に含まれていないか、出現回数が少なすぎます。")

    except Exception as e:
        print(f"Doc2Vecの分析中にエラーが発生しました: {e}")

# --- メイン処理 ---

if __name__ == '__main__':
    try:
        # 指定されたディレクトリから.mdファイルをすべて検索
        search_path = os.path.join(SAMPLE_DIR_PATH, '*.md')
        file_paths = glob.glob(search_path)

        if not file_paths:
            print(f"エラー: サンプル文書が見つかりません。パスを確認してください: {SAMPLE_DIR_PATH}")
        else:
            print(f"{len(file_paths)}件のサンプル文書を読み込みます。")
            all_documents = []
            for path in file_paths:
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
                # テキストを前処理して単語リストに変換
                word_list = preprocess_text_for_doc2vec(text)
                if word_list:
                    all_documents.append(word_list)
            
            if not all_documents:
                print("エラー: テキストから分析対象の単語を抽出できませんでした。")
            else:
                # Doc2Vecで分析を実行
                analyze_with_doc2vec(all_documents)

    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません。パスを確認してください: {SAMPLE_DIR_PATH}")
    except RuntimeError as e:
        print(f"MeCabの実行エラー: {e}")
        print("MeCabまたは辞書が正しくインストールされていない可能性があります。")
    except Exception as e:
        print(f"メイン処理でエラーが発生しました: {e}")
