import os
import pandas as pd
import matplotlib.pyplot as plt
from github import Github
from datetime import datetime, timedelta

# GitHubに接続
g = Github(os.environ["GITHUB_TOKEN"])
repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])

# 各種Issueを取得
issues = repo.get_issues(state="open")

# データフレームに変換するためのリスト
data = []

for issue in issues:
    # ラベル情報を取得
    labels = [label.name for label in issue.labels]
    
    # Issue種別（バグ、機能、タスク）を特定
    issue_type = "その他"
    if "bug" in labels:
        issue_type = "バグ"
    elif "enhancement" in labels:
        issue_type = "機能リクエスト"
    elif "task" in labels:
        issue_type = "タスク"
    
    # 優先度を特定（ボディからパースする必要あり）
    priority = "未設定"
    if "高" in issue.body or "緊急" in issue.body:
        priority = "高"
    elif "中" in issue.body:
        priority = "中"
    elif "低" in issue.body:
        priority = "低"
    
    # データリストに追加
    data.append({
        "番号": issue.number,
        "タイトル": issue.title,
        "種別": issue_type,
        "優先度": priority,
        "作成日": issue.created_at,
        "更新日": issue.updated_at,
        "担当者": issue.assignee.login if issue.assignee else "未割り当て",
    })

# データフレームに変換
df = pd.DataFrame(data)

# 種別ごとの集計
type_counts = df["種別"].value_counts()

# 優先度ごとの集計
priority_counts = df["優先度"].value_counts()

# マークダウンレポートの作成
report = f"""# Issue集計レポート
生成日時: {datetime.now().strftime("%Y/%m/%d %H:%M")}

## 1. 全体概要
- 未解決Issue数: {len(df)}件
- 平均未解決日数: {(datetime.now() - df["作成日"].mean()).days:.1f}日

## 2. 種別ごとの集計
{type_counts.to_markdown()}

## 3. 優先度ごとの集計
{priority_counts.to_markdown()}

## 4. 直近のアクティビティ
直近1週間で更新されたIssue: {len(df[df["更新日"] > datetime.now() - timedelta(days=7)])}件

## 5. 最も長く未解決のIssue（トップ5）
{df.sort_values("作成日").head(5)[["番号", "タイトル", "種別", "優先度", "作成日"]].to_markdown(index=False)}
"""

# レポートをファイルに保存
with open("issue-report.md", "w", encoding="utf-8") as f:
    f.write(report)

# グラフの生成
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
type_counts.plot.bar()
plt.title("種別ごとのIssue数")
plt.tight_layout()

plt.subplot(1, 2, 2)
priority_counts.plot.bar()
plt.title("優先度ごとのIssue数")
plt.tight_layout()

plt.savefig("issue-stats.png")
