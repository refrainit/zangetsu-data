# zangetsu-data

データベース接続とデータ操作のための包括的な Python ライブラリです。複数のデータベースタイプとスプレッドシートに対する統一的なインターフェースを提供します。

## 特徴

- **多様なデータソースサポート**：PostgreSQL、BigQuery、GoogleSpreadsheet など
- **統一インターフェース**：すべてのデータソースで一貫したメソッド呼び出し
- **SQL ファイルテンプレート**：Jinja2 を使用した柔軟な SQL クエリ管理
- **Pandas 統合**：クエリ結果を直接 DataFrame として取得
- **環境変数サポート**：設定の外部化が容易
- **エラーハンドリング**：例外処理とロギング機能の統合
- **スキーマ管理**：テーブル定義の簡単な取得と管理

## インストール

```bash
pip install zangetsu-data
```

## 基本的な使い方

### データベース共通機能

```python
from zangetsu_data.common_database import Database

# データベース接続文字列を指定して接続
db = Database("postgresql://username:password@localhost:5432/mydatabase")

# 接続確立
db.connect()

# クエリの実行とデータの取得
df = db.read_sql("SELECT * FROM users WHERE age > %s", [18])
print(df)

# テーブルリストの取得
tables = db.list_tables()
print(tables)

# リソースの解放
db.close()
```

### PostgreSQL データベース接続

```python
from zangetsu_data.postgresql import Postgresql

# 接続情報を使用してインスタンス作成
db = Postgresql(
    host="localhost",
    port="5432",
    db_name="mydb",
    username="user",
    password="pass"
)

# SQLクエリの実行
df = db.read_sql("SELECT * FROM users")
print(df)

# テーブルリストの取得
tables = db.list_tables()
print(tables)
```

### Google BigQuery 接続

```python
from zangetsu_data.bigquery import BigQuery

# サービスアカウントキーファイルを使用して接続
bq = BigQuery(
    project_id="my-project",
    dataset_id="my_dataset",
    credentials_path="/path/to/service-account-key.json"
)

# クエリの実行
df = bq.read_sql("SELECT * FROM `my_dataset.my_table` LIMIT 1000")
print(df)

# データベース情報の確認
info = bq.show_database_info()
print(info)
```

### Google スプレッドシート操作

```python
from zangetsu_data.spreadsheet import GoogleSpreadsheet

# サービスアカウントキーファイルを使用して接続
gs = GoogleSpreadsheet(
    credentials_path="/path/to/service-account-key.json",
    spreadsheet_id="your_spreadsheet_id"
)

# シートからデータを読み込み
df = gs.read_sheet("Sheet1", "A1:D10")
print(df)

# DataFrameデータをシートに書き込み
import pandas as pd
data_df = pd.DataFrame({"Name": ["Alice", "Bob"], "Score": [85, 92]})
gs.write_sheet(data_df, "Sheet1", "A1", include_header=True)

# データをシートに追加
new_data_df = pd.DataFrame({"Name": ["Charlie"], "Score": [78]})
gs.append_sheet(new_data_df, "Sheet1")

# スプレッドシート内のシート一覧取得
sheets = gs.get_sheet_names()
print(sheets)
```

## SQL テンプレート機能

SQL クエリをファイルとして管理し、テンプレート変数で動的に生成できます。

### ディレクトリ構成

```
your_project/
  ├── app.py
  └── sql/
      ├── users_by_age.sql
      └── orders_summary.sql
```

### SQL ファイル例 (sql/users_by_age.sql)

```sql
SELECT
  id,
  name,
  email,
  age
FROM
  users
WHERE
  age BETWEEN {{ min_age }} AND {{ max_age }}
  {% if status %}
  AND status = '{{ status }}'
  {% endif %}
```

### Python コードでの利用

```python
from zangetsu_data.common_database import Database

db = Database("postgresql://username:password@localhost:5432/mydatabase", sql_dir="sql")

# SQLファイルを読み込み、変数を適用してクエリを取得
sql = db.get_query_from_file("users_by_age", min_age=18, max_age=30, status="active")
print(sql)

# SQLファイルを使用して直接クエリを実行
df = db.execute_query_file(
    "users_by_age",
    {"department": "sales"},  # SQLのプレースホルダに渡すパラメータ
    min_age=20,  # テンプレート変数
    max_age=40
)
print(df)
```

## データベーススキーマ管理

```python
from zangetsu_data.postgresql import Postgresql

db = Postgresql(
    host="localhost",
    port="5432",
    db_name="mydb",
    username="user",
    password="pass"
)

# 特定のテーブルのスキーマ取得
users_schema = db.get_table_schema("users")
print(users_schema)

# データベース内の全テーブルのスキーマ取得
all_schemas = db.get_tables_schema()
print(all_schemas)

# スキーマのDataFrame形式での出力
schema_df = db.export_schema_to_dataframe("users")
print(schema_df)
```

## 環境変数

`/.env`ファイルを使用して設定を外部化できます:

```
# BigQuery Configuration
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json
```

## テーブル操作

```python
from zangetsu_data.common_database import Database

db = Database("postgresql://username:password@localhost:5432/mydatabase")

# 新しいテーブルの作成
db.create_table(
    "employees",
    {
        "id": "SERIAL PRIMARY KEY",
        "name": "VARCHAR(255) NOT NULL",
        "email": "VARCHAR(255) UNIQUE",
        "department": "VARCHAR(100)",
        "hire_date": "DATE"
    }
)

# テーブルの削除
db.delete_table("old_employees")

# トランザクション内での複数クエリの実行
db.transaction_query([
    "INSERT INTO logs (message) VALUES ('Operation started')",
    "UPDATE status SET current = 'processing'",
    "INSERT INTO logs (message) VALUES ('Status updated')"
])
```

## 貢献

1. リポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成
