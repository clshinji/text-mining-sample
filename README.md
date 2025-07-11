# Amazon Comprehend テキスト分析プロジェクト

このプロジェクトは、Amazon Comprehend、Amazon Bedrock、MeCab、Doc2Vecなどの様々な技術を使用して、日本語テキストの分析を行うサンプルコード集です。

## プロジェクト概要

日本語テキストの自然言語処理において、以下の分析手法を比較・検証することを目的としています：

- **Amazon Comprehend**: AWSの自然言語処理サービスを使用したキーフレーズ抽出、エンティティ検出、感情分析
- **Amazon Bedrock**: Claude 4 Sonnetを使用した特徴的な単語抽出
- **MeCab**: 日本語形態素解析による単語頻度分析
- **Doc2Vec**: 文書ベクトル化による類似度分析

## ディレクトリ構成

```
amazon-comprehend/
├── README.md                    # このファイル
├── requirements.txt             # Python依存関係
├── sample-code/                 # サンプルコード
│   ├── comprehend_analysis.py   # Amazon Comprehend分析
│   ├── bedrock_keyword_analyzer.py # Bedrock + ワードクラウド
│   ├── mecab_analysis.py        # MeCab形態素解析
│   ├── doc2vec_analysis.py      # Doc2Vec文書分析
│   └── MEIRYO.TTC              # 日本語フォント（ワードクラウド用）
├── sample-text/                 # 分析対象テキスト
│   ├── sample.md               # メインサンプルテキスト
│   └── sample2.md              # 追加サンプルテキスト
└── _work/                      # 作業用ファイル
    ├── memo.md                 # プロジェクトメモ
    ├── llm.md                  # LLMプロンプトテンプレート
    └── prompt.md               # 詳細プロンプト設計
```

## 必要な環境

### AWS設定
- AWS CLI設定済み
- Amazon Comprehendへのアクセス権限
- Amazon Bedrockへのアクセス権限（Claude 4 Sonnet利用）
- 推奨リージョン: `ap-northeast-1` (東京)

### Python環境
- Python 3.7以上
- 必要なパッケージは `requirements.txt` を参照

## セットアップ

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd amazon-comprehend
```

2. **Python依存関係のインストール**
```bash
pip install -r requirements.txt
```

3. **MeCabのインストール（Ubuntu/Debian）**
```bash
sudo apt-get install mecab mecab-ipadic-utf8 libmecab-dev
```

4. **AWS認証情報の設定**
```bash
aws configure
```

## 使用方法

### 1. Amazon Comprehend分析
```bash
cd sample-code
python comprehend_analysis.py
```
- キーフレーズ抽出
- エンティティ検出
- 感情分析

### 2. Amazon Bedrock + ワードクラウド生成
```bash
cd sample-code
python bedrock_keyword_analyzer.py
```
- Claude 4 Sonnetによる特徴的単語抽出
- 単語出現回数のカウント
- ワードクラウド画像生成

### 3. MeCab形態素解析
```bash
cd sample-code
python mecab_analysis.py
```
- 日本語形態素解析
- 品詞フィルタリング
- 単語頻度分析

### 4. Doc2Vec文書分析
```bash
cd sample-code
python doc2vec_analysis.py
```
- 文書ベクトル化
- 類似度分析

## サンプルテキストについて

`sample-text`ディレクトリには、自然言語処理の分析手法を比較検証するための多様なサンプルテキストが含まれています：

### 一般的なテキストバリエーション
- **ニュース記事風**: 客観的報道文体、エンティティ豊富
- **技術文書・マニュアル風**: 専門用語多数、手順説明中心
- **SNS投稿・口コミ風**: 短文集合、感情表現豊富
- **学術論文・研究報告風**: 論理的構造、客観的分析
- **小説・エッセイ風**: 感情的表現、比喩・修辞技法

### 鉄道技術部門向け専門テキスト
鉄道事業会社の各技術部門（保線、土木、機械、車両、建築、電車線、変電、配電、信号、通信）の実務文書を模したサンプルテキストを収録。専門用語や技術的内容が豊富で、業界特有の表現や構造を含んでいます。

これらの多様なテキストにより、各分析手法の特性や適用範囲を詳細に比較検証することが可能です。

## 出力例

### Amazon Comprehend
- キーフレーズ: "AIアシスタントPro", "音声認識", "タスク管理"
- エンティティ: 人名、組織名、日付
- 感情: ポジティブ/ネガティブ/ニュートラル

### Bedrock + ワードクラウド
- JSON形式での単語頻度データ
- ワードクラウド画像ファイル（PNG）

### MeCab
- 形態素解析結果
- 品詞別単語リスト
- 頻度統計

## 注意事項

- AWS利用料金が発生する可能性があります
- Amazon Bedrockは利用可能なリージョンが限定されています
- MeCabの辞書設定は環境により調整が必要な場合があります
- 大量のテキスト処理時はAPI制限にご注意ください

## ライセンス

このプロジェクトはサンプルコードとして提供されています。商用利用の際は適切なライセンス確認を行ってください。

## 貢献

バグ報告や機能改善の提案は、Issueまたはプルリクエストでお願いします。

## 関連リンク

- [Amazon Comprehend Documentation](https://docs.aws.amazon.com/comprehend/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [MeCab Documentation](https://taku910.github.io/mecab/)
- [Gensim Doc2Vec](https://radimrehurek.com/gensim/models/doc2vec.html)
