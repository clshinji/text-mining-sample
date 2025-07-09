import boto3
import os

# --- 設定 ---
# SageMaker Notebookインスタンスから実行する場合、ロールにComprehendへのアクセス権があれば
# access_key, secret_key, region_name の設定は不要です。
# boto3が自動的に認証情報を解決します。
REGION_NAME = "ap-northeast-1" # 例: 東京リージョン

# 分析対象のサンプルファイル
# このスクリプトを `sample-code` ディレクトリに配置した場合の相対パス
# SageMakerのノートブックから実行する際は、適宜パスを調整してください。
FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'sample-text', 'sample.md')

# --- 関数定義 ---

def analyze_text_with_comprehend(text, region_name):
    """
    Amazon Comprehend を使ってテキスト分析を実行する関数。
    - キーフレーズの検出
    - エンティティの検出
    - 感情の分析
    """
    try:
        # Comprehend クライアントの作成
        comprehend = boto3.client("comprehend", region_name=region_name)
        language_code = 'ja'

        # --- 1. キーフレーズ分析 ---
        print("--- 1. Amazon Comprehendによるキーフレーズ分析 ---")
        key_phrases_response = comprehend.detect_key_phrases(Text=text, LanguageCode=language_code)
        print("検出されたキーフレーズ:")
        if key_phrases_response['KeyPhrases']:
            for phrase in key_phrases_response['KeyPhrases']:
                print(f"- {phrase['Text']} (スコア: {phrase['Score']:.4f})")
        else:
            print("キーフレーズは見つかりませんでした。")
        
        print("\n" + "="*50 + "\n")

        # --- 2. エンティティ検出 ---
        print("--- 2. Amazon Comprehendによるエンティティ検出 ---")
        entities_response = comprehend.detect_entities(Text=text, LanguageCode=language_code)
        print("検出されたエンティティ:")
        if entities_response['Entities']:
            for entity in entities_response['Entities']:
                print(f"- {entity['Text']} (タイプ: {entity['Type']}, スコア: {entity['Score']:.4f})")
        else:
            print("エンティティは見つかりませんでした。")

        print("\n" + "="*50 + "\n")

        # --- 3. 感情分析 ---
        print("--- 3. Amazon Comprehendによる感情分析 ---")
        sentiment_response = comprehend.detect_sentiment(Text=text, LanguageCode=language_code)
        print(f"全体の感情: {sentiment_response['Sentiment']}")
        print("感情スコア:")
        for sentiment, score in sentiment_response['SentimentScore'].items():
            print(f"- {sentiment}: {score:.4f}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

# --- メイン処理 ---

if __name__ == '__main__':
    try:
        # サンプルテキストファイルを読み込む
        # ノートブック環境で実行しやすいように、絶対パスで指定しています。
        # 必要に応じてパスを調整してください。
        absolute_file_path = "/workspaces/esio/amazon-comprehend/sample-text/sample.md"
        with open(absolute_file_path, 'r', encoding='utf-8') as f:
            sample_text = f.read()
        
        # テキストが5000バイトを超えている場合は分割する必要があるが、今回はサンプルなので全体を一度に処理
        if len(sample_text.encode('utf-8')) > 4800: # 念のため少し余裕を持たせる
            print("警告: テキストサイズが大きいため、一部を切り詰めて分析します。")
            # UTF-8でエンコードしてからバイト数を基準に切り詰める
            encoded_text = sample_text.encode('utf-8')
            truncated_encoded_text = encoded_text[:4800]
            # 不完全なマルチバイト文字で終わらないようにデコード・再エンコード
            sample_text = truncated_encoded_text.decode('utf-8', 'ignore')


        # Comprehendで分析を実行
        analyze_text_with_comprehend(sample_text, REGION_NAME)

    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません。パスを確認してください: {absolute_file_path}")
    except Exception as e:
        print(f"メイン処理でエラーが発生しました: {e}")
