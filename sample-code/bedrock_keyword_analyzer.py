#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amazon Bedrock を使用したテキスト分析サンプル
Claude 4 Sonnet で特徴的な単語を抽出し、出現回数をカウントします
"""

import boto3
import json
import re
from datetime import datetime
from wordcloud import WordCloud
import matplotlib.pyplot as plt

def extract_json_from_text(text):
    """
    テキストからJSONを抽出する関数
    LLMの出力にJSON以外のテキストが含まれている場合に対応
    """
    # 複数のパターンでJSONを探す
    patterns = [
        # パターン1: 最初の{から最後の}まで
        r'\{.*\}',
        # パターン2: ```json ブロック内
        r'```json\s*(\{.*?\})\s*```',
        # パターン3: ``` ブロック内
        r'```\s*(\{.*?\})\s*```'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                # JSONとして解析を試行
                parsed = json.loads(match)
                return parsed
            except json.JSONDecodeError:
                continue
    
    # 行ごとに分割してJSONらしい行を探す
    lines = text.split('\n')
    json_lines = []
    in_json = False
    brace_count = 0
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('{'):
            in_json = True
            json_lines = [line]
            brace_count = line.count('{') - line.count('}')
        elif in_json:
            json_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count <= 0:
                break
    
    if json_lines:
        try:
            json_text = '\n'.join(json_lines)
            return json.loads(json_text)
        except json.JSONDecodeError:
            pass
    
    return None

def create_wordcloud(word_frequency, top_n=10):
    """
    単語の出現回数からワードクラウドを生成する関数
    """
    # 上位N位までの単語を取得
    top_words = dict(list(word_frequency.items())[:top_n])
    
    if not top_words:
        print("❌ ワードクラウド用のデータがありません")
        return
    
    print(f"🎨 上位{top_n}位までの単語でワードクラウドを生成中...")
    
    try:
        # 日本語フォントファイルのパスを指定
        font_path = "./MEIRYO.TTC"
        
        # ワードクラウドを生成
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            max_words=top_n,
            relative_scaling=0.5,
            colormap='viridis',
            font_path=font_path  # MEIRYOフォントを指定
        ).generate_from_frequencies(top_words)
        
        # プロット設定（日本語フォント対応）
        plt.rcParams['font.family'] = 'DejaVu Sans'  # 英語部分用
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'Word Frequency Ranking Top {top_n}', fontsize=16, pad=20)
        
        # ファイルに保存
        output_file = "wordcloud_result.png"
        plt.savefig(output_file, bbox_inches='tight', dpi=300)
        print(f"✅ ワードクラウドを {output_file} に保存しました")
        
        # 画面に表示
        plt.show()
        
    except FileNotFoundError:
        print("❌ MEIRYO.TTCフォントファイルが見つかりません")
        print("💡 カレントディレクトリにMEIRYO.TTCファイルがあることを確認してください")
    except Exception as e:
        print(f"❌ ワードクラウド生成でエラーが発生しました: {e}")

def analyze_text_with_bedrock():
    """
    メイン分析関数：テキストファイルを読み込み、Bedrockで分析し、結果を出力
    """
    
    # 1. 設定
    # Claude 4 Sonnet用の推論プロファイルIDを使用
    MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    REGION = "us-east-1"
    
    print("🚀 Amazon Bedrock テキスト分析を開始します...")
    
    # 2. テキストファイルを読み込み
    try:
        with open("../sample-text/sample.md", "r", encoding="utf-8") as file:
            sample_text = file.read()
        print("✅ サンプルテキストを読み込みました")
    except FileNotFoundError:
        print("❌ sample.mdファイルが見つかりません")
        return
    
    # 3. プロンプトテンプレートを読み込み
    try:
        with open("../_work/llm.md", "r", encoding="utf-8") as file:
            prompt_template = file.read()
        print("✅ プロンプトテンプレートを読み込みました")
    except FileNotFoundError:
        print("❌ llm.mdファイルが見つかりません")
        return
    
    # 4. Bedrockクライアントを作成
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name=REGION
    )
    print("✅ Bedrockクライアントを初期化しました")
    
    # 5. プロンプトを作成（テンプレートにテキストを埋め込み）
    prompt = prompt_template.replace("{{解析対象のテキストをLLMに渡す}}", sample_text)
    
    # 6. Bedrock converse_stream APIを呼び出し
    try:
        print("🤖 Claude 4 Sonnet で分析中...")
        
        response = bedrock_runtime.converse_stream(
            modelId=MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            inferenceConfig={
                "maxTokens": 2000,
                "temperature": 0.1
            }
        )
        
        # ストリーミングレスポンスを収集
        llm_output = ""
        for event in response["stream"]:
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"]["delta"]
                if "text" in delta:
                    llm_output += delta["text"]
        
        print("✅ LLMからの応答を取得しました")
        print(f"📄 LLM出力プレビュー: {llm_output[:200]}...")
        
    except Exception as e:
        print(f"❌ Bedrock API呼び出しでエラーが発生しました: {e}")
        return
    
    # 7. LLMの出力からJSONを抽出（堅牢なパース処理）
    try:
        print("🔍 JSON形式のデータを抽出中...")
        
        # 堅牢なJSON抽出を実行
        keywords_data = extract_json_from_text(llm_output)
        
        if keywords_data is None:
            print("❌ 有効なJSONが見つかりませんでした")
            print(f"LLM完全出力:\n{llm_output}")
            return
        
        # resultsキーから単語配列を取得
        if "results" not in keywords_data:
            print("❌ 'results'キーが見つかりません")
            print(f"取得したJSON: {keywords_data}")
            return
            
        keywords = keywords_data["results"]
        print(f"✅ {len(keywords)}個の特徴的な単語を抽出しました")
        print(f"📝 抽出された単語: {keywords}")
        
    except Exception as e:
        print(f"❌ JSON解析でエラーが発生しました: {e}")
        print(f"LLM完全出力:\n{llm_output}")
        return
    
    # 8. 各単語の出現回数をカウント
    print("🔍 単語の出現回数をカウント中...")
    
    word_count = {}
    for keyword in keywords:
        # 正規表現で単語の出現回数をカウント（大文字小文字を区別しない）
        pattern = re.escape(keyword)
        matches = re.findall(pattern, sample_text, re.IGNORECASE)
        count = len(matches)
        word_count[keyword] = count
        print(f"  📝 '{keyword}': {count}回")
    
    # 9. 出現回数の多い順に並び替え
    print("📊 出現回数の多い順に並び替え中...")
    sorted_word_count = dict(sorted(word_count.items(), key=lambda x: x[1], reverse=True))
    
    print("🏆 出現回数ランキング:")
    for i, (word, count) in enumerate(sorted_word_count.items(), 1):
        print(f"  {i}位: '{word}' - {count}回")
    
    # 10. 結果をJSON形式で出力
    result = {
        "analysis_timestamp": datetime.now().isoformat(),
        "source_file": "sample-text/sample.md",
        "model_used": MODEL_ID,
        "extracted_keywords": keywords,
        "word_frequency": sorted_word_count,  # 並び替え済みの辞書を使用
        "word_frequency_ranking": [
            {"rank": i, "word": word, "count": count} 
            for i, (word, count) in enumerate(sorted_word_count.items(), 1)
        ],
        "total_words_analyzed": len(keywords)
    }
    
    print("\n" + "="*50)
    print("📊 分析結果（JSON形式）")
    print("="*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 11. 結果をファイルに保存
    output_file = "analysis_result.json"
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 結果を {output_file} に保存しました")
    
    # 12. ワードクラウドを生成
    create_wordcloud(sorted_word_count, top_n=10)
    
    print("🎉 分析完了！")

if __name__ == "__main__":
    analyze_text_with_bedrock()
