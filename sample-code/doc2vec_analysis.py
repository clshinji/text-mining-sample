import os
import glob
import MeCab
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import numpy as np
import re
import time
from collections import Counter
import json

# --- 設定 ---
MECAB_ARGS = ""
SAMPLE_DIR_PATH = "sample-text/"

# ハンズオン向け設定
MAX_FILES = 5  # 適度なファイル数
MAX_TEXT_LENGTH = 3000  # 十分な分析データ
EPOCHS = 15  # バランスの取れたエポック数
MIN_COUNT = 2
VECTOR_SIZE = 100

class Doc2VecAnalyzer:
    def __init__(self):
        self.model = None
        self.documents = []
        self.document_names = []
        self.word_stats = {}
        
    def preprocess_text(self, text, doc_name):
        """
        高品質な前処理：統計情報も収集
        """
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
        
        tagger = MeCab.Tagger(MECAB_ARGS)
        tagger.parse('')
        node = tagger.parseToNode(text)
        
        words = []
        pos_stats = Counter()
        
        # 拡張されたstop wordsリスト
        stop_words = {
            # 基本的な機能語
            'こと', 'もの', 'ため', 'これ', 'それ', 'あれ', 'どれ', 'よう', 'さん', 'ところ',
            'とき', 'とこ', 'など', 'なに', 'なん', 'どこ', 'いつ', 'だれ', 'どう', 'なぜ',
            
            # 代名詞・指示語
            '私', '僕', '俺', '君', '彼', '彼女', 'あなた', 'みなさん', 'みんな',
            'ここ', 'そこ', 'あそこ', 'どこか', 'いま', 'いつか', 'どこでも',
            
            # 助詞的な名詞
            '上', '下', '中', '前', '後', '左', '右', '横', '隣', '間', '内', '外',
            '先', '奥', '手前', '向こう', '以上', '以下', '未満', '程度', '以外',
            
            # 時間・頻度表現
            '今日', '昨日', '明日', '今年', '去年', '来年', '今月', '先月', '来月',
            '毎日', '毎回', '毎年', '毎月', '毎週', '常に', 'いつも', 'たまに',
            
            # 数量・程度表現
            '全て', '全部', 'すべて', '一部', '半分', '大部分', '少し', 'ちょっと',
            'かなり', 'とても', 'すごく', 'めちゃくちゃ', '非常', '極めて',
            
            # 接続・転換表現
            'しかし', 'でも', 'だが', 'ただし', 'ところが', 'けれど', 'けれども',
            'そして', 'また', 'さらに', 'それから', 'それで', 'そこで', 'つまり',
            
            # 感嘆・応答表現
            'はい', 'いいえ', 'ええ', 'うん', 'そう', 'そうです', 'なるほど',
            'おお', 'ああ', 'うーん', 'えー', 'まあ', 'やはり', 'やっぱり',
            
            # 一般的すぎる動詞・形容詞の語幹
            'する', 'なる', 'ある', 'いる', 'できる', 'みる', 'いく', 'くる',
            'いい', 'よい', '悪い', '大きい', '小さい', '新しい', '古い',
            
            # ビジネス・技術文書でよく出る一般語
            '場合', '状況', '状態', '方法', '手段', '方式', '形式', '種類', '方向',
            '結果', '効果', '影響', '関係', '関連', '対象', '目的', '理由', '原因',
            '問題', '課題', '解決', '改善', '向上', '発展', '進歩', '変化', '変更',
            
            # 単位・助数詞的表現
            '個', '本', '枚', '台', '人', '回', '度', '倍', '割', 'パーセント',
            '時間', '分', '秒', '日', '週間', 'ヶ月', '年間', 'メートル', 'キロ'
        }

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

            # 統計収集
            pos_stats[pos] += 1

            # 高品質な品詞選択
            target_pos = ['名詞', '動詞', '形容詞']
            if pos in target_pos:
                word_to_check = original_form if pos in ['動詞', '形容詞'] else surface_form
                
                # 高品質フィルタリング
                if (word_to_check != '*' and 
                    word_to_check not in stop_words and 
                    len(word_to_check) > 1 and
                    not re.match(r'^[0-9]+$', word_to_check) and  # 数字のみ除外
                    pos != '名詞' or pos_detail1 not in ['数', '非自立', '代名詞']):
                    words.append(word_to_check)

            node = node.next
        
        # 文書統計を保存
        self.word_stats[doc_name] = {
            'total_words': len(words),
            'unique_words': len(set(words)),
            'pos_distribution': dict(pos_stats.most_common(5))
        }
        
        return words

    def train_model(self, documents, document_names):
        """
        Doc2Vecモデルの学習
        """
        print("=== Doc2Vec モデル学習フェーズ ===")
        
        tagged_documents = [
            TaggedDocument(doc, [name]) 
            for doc, name in zip(documents, document_names)
        ]
        
        self.model = Doc2Vec(
            vector_size=VECTOR_SIZE,
            min_count=MIN_COUNT,
            epochs=EPOCHS,
            workers=min(4, os.cpu_count()),
            dm=1,  # PV-DM (分散メモリ)
            window=5,
            alpha=0.025,
            min_alpha=0.00025
        )
        
        start_time = time.time()
        self.model.build_vocab(tagged_documents)
        
        print(f"学習開始: {len(documents)}文書, 語彙数: {len(self.model.wv.key_to_index)}")
        self.model.train(tagged_documents, total_examples=self.model.corpus_count, epochs=self.model.epochs)
        
        training_time = time.time() - start_time
        print(f"学習完了 (所要時間: {training_time:.2f}秒)")
        
        return self.model

    def analyze_document_similarity(self):
        """
        文書間類似度分析
        """
        print("\n=== 文書間類似度分析 ===")
        
        if len(self.document_names) < 2:
            print("類似度分析には2つ以上の文書が必要です。")
            return
        
        similarities = []
        for i, doc1 in enumerate(self.document_names):
            for j, doc2 in enumerate(self.document_names[i+1:], i+1):
                try:
                    similarity = self.model.dv.similarity(doc1, doc2)
                    similarities.append((doc1, doc2, similarity))
                    print(f"{os.path.basename(doc1)} ⟷ {os.path.basename(doc2)}: {similarity:.4f}")
                except KeyError as e:
                    print(f"文書ベクトルが見つかりません: {e}")
        
        # 最も類似した文書ペア
        if similarities:
            most_similar = max(similarities, key=lambda x: x[2])
            print(f"\n最も類似した文書ペア:")
            print(f"  {os.path.basename(most_similar[0])} ⟷ {os.path.basename(most_similar[1])}")
            print(f"  類似度: {most_similar[2]:.4f}")

    def analyze_word_similarity(self):
        """
        単語類似度分析（教育的な解説付き）
        """
        print("\n=== 単語類似度分析 ===")
        
        # 語彙から頻出単語を選択
        word_freq = Counter()
        for doc in self.documents:
            word_freq.update(doc)
        
        common_words = [word for word, freq in word_freq.most_common(20) 
                       if word in self.model.wv.key_to_index]
        
        if not common_words:
            print("分析可能な単語が見つかりません。")
            return
        
        print(f"頻出単語から分析対象を選択: {common_words[:5]}")
        
        for word in common_words[:3]:
            print(f"\n'{word}' の類似単語:")
            try:
                similar_words = self.model.wv.most_similar(word, topn=5)
                for i, (sim_word, similarity) in enumerate(similar_words, 1):
                    print(f"  {i}. {sim_word} (類似度: {similarity:.4f})")
            except KeyError:
                print(f"  '{word}' の類似単語を見つけられませんでした。")

    def analyze_word_clusters(self):
        """
        単語クラスタリング分析
        """
        print("\n=== 単語クラスタリング分析 ===")
        
        # 頻出単語のベクトルを取得
        word_freq = Counter()
        for doc in self.documents:
            word_freq.update(doc)
        
        target_words = [word for word, freq in word_freq.most_common(15) 
                       if word in self.model.wv.key_to_index]
        
        if len(target_words) < 3:
            print("クラスタリングに十分な単語がありません。")
            return
        
        print(f"分析対象単語: {target_words}")
        
        # 簡易クラスタリング（類似度ベース）
        clusters = {}
        processed = set()
        
        for word in target_words:
            if word in processed:
                continue
                
            cluster = [word]
            processed.add(word)
            
            try:
                similar_words = self.model.wv.most_similar(word, topn=10)
                for sim_word, similarity in similar_words:
                    if sim_word in target_words and similarity > 0.3 and sim_word not in processed:
                        cluster.append(sim_word)
                        processed.add(sim_word)
                
                if len(cluster) > 1:
                    clusters[f"クラスタ_{len(clusters)+1}"] = cluster
            except KeyError:
                continue
        
        print("\n単語クラスタ:")
        for cluster_name, words in clusters.items():
            print(f"  {cluster_name}: {', '.join(words)}")

    def generate_analysis_report(self):
        """
        分析レポートの生成
        """
        print("\n" + "="*60)
        print("=== Doc2Vec 分析レポート ===")
        print("="*60)
        
        print(f"\n【モデル情報】")
        print(f"  ベクトル次元数: {self.model.vector_size}")
        print(f"  語彙数: {len(self.model.wv.key_to_index)}")
        print(f"  学習エポック数: {self.model.epochs}")
        
        print(f"\n【文書統計】")
        for doc_name, stats in self.word_stats.items():
            print(f"  {os.path.basename(doc_name)}:")
            print(f"    総単語数: {stats['total_words']}")
            print(f"    ユニーク単語数: {stats['unique_words']}")
            print(f"    語彙多様性: {stats['unique_words']/stats['total_words']:.3f}")
        
        print(f"\n【頻出単語トップ10】")
        word_freq = Counter()
        for doc in self.documents:
            word_freq.update(doc)
        
        for i, (word, freq) in enumerate(word_freq.most_common(10), 1):
            print(f"  {i:2d}. {word} ({freq}回)")

def main():
    """
    メイン処理
    """
    analyzer = Doc2VecAnalyzer()
    
    try:
        start_time = time.time()
        
        # ファイル読み込み
        search_path = os.path.join(SAMPLE_DIR_PATH, '*.md')
        file_paths = glob.glob(search_path)
        
        if not file_paths:
            print(f"エラー: サンプル文書が見つかりません: {SAMPLE_DIR_PATH}")
            return
        
        # ファイル数制限
        limited_files = file_paths[:MAX_FILES]
        print(f"=== ファイル読み込み ===")
        print(f"対象ファイル数: {len(limited_files)}")
        
        documents = []
        document_names = []
        
        for i, path in enumerate(limited_files):
            filename = os.path.basename(path)
            print(f"処理中: {filename} ({i+1}/{len(limited_files)})")
            
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            words = analyzer.preprocess_text(text, path)
            if words:
                documents.append(words)
                document_names.append(path)
                print(f"  抽出単語数: {len(words)}")
        
        if not documents:
            print("エラー: 分析可能な文書がありません。")
            return
        
        analyzer.documents = documents
        analyzer.document_names = document_names
        
        # モデル学習
        analyzer.train_model(documents, document_names)
        
        # 各種分析実行
        analyzer.analyze_document_similarity()
        analyzer.analyze_word_similarity()
        analyzer.analyze_word_clusters()
        analyzer.generate_analysis_report()
        
        total_time = time.time() - start_time
        print(f"\n総処理時間: {total_time:.2f}秒")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
