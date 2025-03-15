"""
データベース接続の共通親クラスを定義するモジュール。

このモジュールは、SQLAlchemyを使用したデータベース操作を抽象化し、
共通的なデータベース操作メソッドを提供します。
また、Jinja2テンプレートを使用したSQLクエリ管理機能を含みます。
"""

import inspect
import os
from typing import Any

import jinja2
import pandas as pd
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import Engine
from zangetsu_logger import initialize


class Database:
    """
    データベース接続と基本的な操作を管理するクラス。

    このクラスは、データベース接続の確立、クエリの実行、テーブル操作などの
    共通的な機能を提供します。また、Jinja2テンプレートを使用したSQLクエリ管理も行います。

    Attributes:
        engine (Engine): SQLAlchemyのデータベースエンジン。
        connection: データベース接続オブジェクト。
        sql_dir (str): SQLクエリファイルが格納されているディレクトリパス。
        jinja_env (jinja2.Environment): Jinja2テンプレートエンジン。

    Examples:
        # データベース接続文字列を使用してインスタンスを作成
        >>> db = Database('postgresql://username:password@localhost:5432/mydatabase')
        >>> db.connect()

        # テーブルのリストを取得
        >>> tables = db.list_tables()
        >>> print(tables)

        # SQLクエリを実行してデータを取得
        >>> df = db.read_sql('SELECT * FROM users')
        >>> print(df)

        # SQLファイルを使用してクエリを実行
        >>> df = db.execute_query_file('users_by_age', {'min_age': 18})
        >>> print(df)
    """

    def __init__(self, connection_string: str, sql_dir: str = "sql"):
        self.logger = initialize()
        self.engine: Engine = sqlalchemy.create_engine(connection_string)
        self.connection = None
        self.connection_string = connection_string

        # 呼び出し元のモジュールを特定してプロジェクトルートを見つける
        caller_frame = inspect.stack()[2]
        caller_module = inspect.getmodule(caller_frame[0])

        # 呼び出し元モジュールのディレクトリを取得（リポジトリルートの可能性が高い）
        if caller_module and hasattr(caller_module, "__file__"):
            # 呼び出し元ディレクトリをプロジェクトルートとして使用
            project_root = os.path.dirname(os.path.abspath(caller_module.__file__))
        else:
            # フォールバック: カレントディレクトリを使用
            project_root = os.getcwd()

        # SQLクエリファイルディレクトリを設定
        self.sql_dir = os.path.join(project_root, sql_dir)
        self.logger.debug(f"SQLディレクトリ: {self.sql_dir}")

        # Jinja2環境の設定
        if os.path.exists(self.sql_dir):  # 絶対パスでチェック
            self.jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(self.sql_dir),  # 絶対パスを使用
                autoescape=jinja2.select_autoescape(["sql"]),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self.logger.warning(
                f"SQLディレクトリ '{self.sql_dir}' が見つかりません。execute_query_file()を使用する前にディレクトリを作成してください。"
            )
            self.jinja_env = None

    def connect(self) -> None:
        """
        データベース接続を確立する。

        既存の接続が存在しない場合のみ、新しい接続を作成する。

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> db.connect()  # データベースに接続
        """
        if not self.connection:
            self.connection = self.engine.connect()

    def close(self) -> None:
        """
        データベース接続を閉じる。

        有効な接続が存在する場合、接続を閉じてNoneに設定する。

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> db.connect()
            >>> db.close()  # 接続を閉じる
        """
        if self.connection:
            self.connection.close()
            self.connection = None

    def show_database_info(self) -> pd.DataFrame:
        """
        データベース接続の情報をDataFrameとして返す。

        Returns:
            pd.DataFrame: データベースエンジンの接続情報を含むDataFrame。

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> info_df = db.show_database_info()
            >>> print(info_df)
        """
        info_str = str(self.engine)
        return pd.DataFrame({"database_info": [info_str]})

    def read_sql(self, sql: str, params=None) -> pd.DataFrame:
        """
        SQLクエリを実行し、結果をPandasのDataFrameとして返す。

        Args:
            sql (str): 実行するSQLクエリ文字列。
            params (list or dict, optional): SQLクエリに渡すパラメータ。

        Returns:
            pd.DataFrame: クエリ結果を含むDataFrame。エラー発生時は空のDataFrameを返す。

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> df = db.read_sql('SELECT * FROM users WHERE age > %s', [18])
            >>> print(df)
        """
        try:
            if params:
                return pd.read_sql_query(sql, self.engine, params=params)
            else:
                return pd.read_sql_query(sql, self.engine)
        except Exception as e:
            print(f"データベースからデータを読み取る際にエラーが発生しました: {e}")
            return pd.DataFrame()

    def list_tables(self) -> pd.DataFrame:
        """
        データベース内のテーブル名のリストをDataFrameとして取得する。

        Returns:
            pd.DataFrame: データベース内のテーブル名を含むDataFrame。

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> tables_df = db.list_tables()
            >>> print(tables_df)
        """
        inspector = sqlalchemy.inspect(self.engine)
        tables = inspector.get_table_names()
        return pd.DataFrame({"table_name": tables})

    def create_table(self, table_name: str, columns: dict) -> pd.DataFrame:
        """
        指定された名前とカラム定義で新しいテーブルを作成する。

        Args:
            table_name (str): 作成するテーブルの名前。
            columns (dict): カラム名とデータ型の辞書。
                キーはカラム名、値はデータ型と制約を含む文字列。

        Returns:
            pd.DataFrame: 操作の結果を含むDataFrame。

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> result_df = db.create_table('users', {
            ...     'id': 'SERIAL PRIMARY KEY',
            ...     'name': 'VARCHAR(255)',
            ...     'email': 'VARCHAR(255) UNIQUE'
            ... })
            >>> print(result_df)
        """
        status = "success"
        message = f"テーブル {table_name} が正常に作成されました"

        try:
            if not self.connection:
                self.connect()
            column_definitions = ", ".join(
                [f"{name} {data_type}" for name, data_type in columns.items()]
            )
            self.connection.execute(
                text(f"CREATE TABLE {table_name} ({column_definitions})")
            )
            self.connection.commit()
        except Exception as e:
            status = "error"
            message = f"テーブル {table_name} の作成中にエラーが発生しました: {e}"
            print(message)
            self.connection.rollback()

        return pd.DataFrame({"status": [status], "message": [message]})

    def delete_table(self, table_name: str) -> pd.DataFrame:
        """
        指定されたテーブルを削除する。

        Args:
            table_name (str): 削除するテーブルの名前。

        Returns:
            pd.DataFrame: 操作の結果を含むDataFrame。

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> result_df = db.delete_table('old_users')
            >>> print(result_df)
        """
        status = "success"
        message = f"テーブル {table_name} が正常に削除されました"

        try:
            if not self.connection:
                self.connect()
            self.connection.execute(text(f"DROP TABLE {table_name}"))
            self.connection.commit()
        except Exception as e:
            status = "error"
            message = f"テーブル {table_name} の削除中にエラーが発生しました: {e}"
            print(message)
            self.connection.rollback()

        return pd.DataFrame({"status": [status], "message": [message]})

    def query(self, sql: str) -> pd.DataFrame:
        """
        与えられたSQLクエリを実行し、結果をDataFrameとして返す。

        Args:
            sql (str): 実行するSQLクエリ文字列。

        Returns:
            pd.DataFrame: クエリ結果を含むDataFrame。結果がない場合は操作状況を含むDataFrame。

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> result_df = db.query('UPDATE users SET status = "active" WHERE id = 1')
            >>> print(result_df)
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(sql))
                connection.commit()

                # SELECTクエリの場合、結果をDataFrameとして返す
                if sql.strip().upper().startswith("SELECT"):
                    return pd.DataFrame(result.fetchall(), columns=result.keys())
                # 他のタイプのクエリの場合、影響を受けた行数を含むDataFrameを返す
                else:
                    return pd.DataFrame(
                        {
                            "status": ["success"],
                            "message": ["クエリが正常に実行されました"],
                            "rows_affected": [result.rowcount],
                        }
                    )
        except Exception as e:
            message = f"クエリの実行中にエラーが発生しました: {e}"
            print(message)
            return pd.DataFrame({"status": ["error"], "message": [message]})

    def transaction_query(self, queries: list[str]) -> pd.DataFrame:
        """
        複数のSQLクエリをトランザクション内で実行する。

        Args:
            queries (list[str]): 実行するSQLクエリの文字列リスト。

        Returns:
            pd.DataFrame: トランザクション結果を含むDataFrame。

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> result_df = db.transaction_query([
            ...     'INSERT INTO users (name, email) VALUES ("John", "john@example.com")',
            ...     'UPDATE accounts SET balance = balance - 100 WHERE user_id = 1'
            ... ])
            >>> print(result_df)
        """
        try:
            results = []
            with self.engine.begin() as connection:
                for query in queries:
                    result = connection.execute(text(query))
                    results.append({"query": query, "rows_affected": result.rowcount})
                connection.commit()

            return pd.DataFrame(results)
        except Exception as e:
            message = f"トランザクション実行中にエラーが発生しました: {e}"
            print(message)
            return pd.DataFrame({"status": ["error"], "message": [message]})

    def get_query_from_file(self, query_name: str, **kwargs) -> str:
        """
        指定された名前のSQLクエリファイルを読み込み、Jinja2テンプレートとして処理する。

        Args:
            query_name (str): クエリファイル名（.sqlは省略可能）
            **kwargs: テンプレート変数の値

        Returns:
            str: 処理済みのSQL文字列

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> sql = db.get_query_from_file('users_by_age', min_age=18, max_age=65)
            >>> print(sql)
        """
        if self.jinja_env is None:
            raise ValueError(f"SQLディレクトリ '{self.sql_dir}' が見つかりません。")

        # .sql拡張子の追加
        if not query_name.endswith(".sql"):
            query_name += ".sql"

        try:
            # テンプレートを取得して変数を適用
            template = self.jinja_env.get_template(query_name)
            return template.render(**kwargs)
        except jinja2.exceptions.TemplateNotFound:
            raise FileNotFoundError(
                f"クエリファイル '{query_name}' が '{self.sql_dir}' ディレクトリ内に見つかりません。"
            )
        except Exception as e:
            raise ValueError(f"SQLテンプレートの処理中にエラーが発生しました: {e}")

    def execute_query_file(
        self, query_name: str, params: dict[str, Any] | None = None, **kwargs
    ) -> pd.DataFrame:
        """
        指定されたSQLファイルを読み込み、Jinja2テンプレートとして処理して実行する。

        Args:
            query_name (str): クエリファイル名（.sqlは省略可能）
            params (dict, optional): SQLクエリのプレースホルダに渡すパラメータ
            **kwargs: Jinja2テンプレート変数に渡す値

        Returns:
            pd.DataFrame: クエリ実行結果を含むDataFrame

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> # 年齢フィルターを使用するクエリを実行
            >>> df = db.execute_query_file('users_by_age', {'status': 'active'}, min_age=18, max_age=65)
            >>> print(df)
        """
        try:
            # テンプレートからSQLを取得
            sql = self.get_query_from_file(query_name, **kwargs)

            # SQLを実行
            return self.read_sql(sql, params)
        except FileNotFoundError as e:
            message = str(e)
            print(message)
            return pd.DataFrame({"status": ["error"], "message": [message]})
        except Exception as e:
            message = f"SQLファイルの実行中にエラーが発生しました: {e}"
            print(message)
            return pd.DataFrame({"status": ["error"], "message": [message]})

    def get_table_schema(self, table_name: str) -> pd.DataFrame:
        """
        指定されたテーブルのスキーマ情報を取得する。

        Args:
            table_name (str): スキーマ情報を取得するテーブル名。

        Returns:
            pd.DataFrame: テーブルの列情報を含むDataFrame。
            各行には以下の列が含まれます：
            - name: 列名
            - type: データ型
            - nullable: NULLを許可するかどうか
            - default: デフォルト値
            - primary_key: 主キーかどうか

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> schema_df = db.get_table_schema('users')
            >>> print(schema_df)
        """
        try:
            # SQLファイルからスキーマ情報を取得
            results_df = self.execute_sql_file(
                "db/sql/get_table_schema.sql", {"table_name": table_name}
            )

            # 結果がエラーの場合（status列が存在する場合）
            if (
                "status" in results_df.columns
                and "error" in results_df["status"].values
            ):
                return results_df

            # 列名を適切に変更
            if len(results_df.columns) >= 5:
                results_df.columns = [
                    "name",
                    "type",
                    "nullable",
                    "default",
                    "primary_key",
                ]

            # table_name列を追加
            results_df["table_name"] = table_name

            return results_df

        except Exception as e:
            message = (
                f"テーブル {table_name} のスキーマ取得中にエラーが発生しました: {e}"
            )
            print(message)
            return pd.DataFrame({"status": ["error"], "message": [message]})

    def get_tables_schema(self) -> pd.DataFrame:
        """
        データベース内の全テーブルのスキーマ情報を取得する。

        Returns:
            pd.DataFrame: 全テーブルのスキーマ情報を含むDataFrame。

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> all_schemas_df = db.get_tables_schema()
            >>> print(all_schemas_df)
        """
        try:
            # テーブル一覧を取得
            tables_df = self.list_tables()

            # 全テーブルのスキーマ情報を格納するリスト
            all_schema_data = []

            # 各テーブルのスキーマを取得して結合
            for table_name in tables_df["table_name"]:
                table_schema_df = self.get_table_schema(table_name)

                # エラーでなければ結果をリストに追加
                if "status" not in table_schema_df.columns:
                    all_schema_data.append(table_schema_df)

            # 空のリストでなければDataFrameを結合
            if all_schema_data:
                return pd.concat(all_schema_data, ignore_index=True)
            else:
                return pd.DataFrame(
                    {
                        "status": ["warning"],
                        "message": [
                            "テーブルが見つからないか、スキーマ情報を取得できませんでした"
                        ],
                    }
                )

        except Exception as e:
            message = f"テーブルスキーマの取得中にエラーが発生しました: {e}"
            print(message)
            return pd.DataFrame({"status": ["error"], "message": [message]})

    def export_schema_to_dataframe(self, table_name: str | None = None) -> pd.DataFrame:
        """
        テーブルのスキーマ情報をPandas DataFrameとしてエクスポートする。

        Args:
            table_name (str | None, optional): スキーマを取得するテーブル名。
                指定しない場合は全テーブルのスキーマを取得。

        Returns:
            pd.DataFrame: テーブルスキーマ情報を含むDataFrame。

        Examples:
            >>> db = Database('postgresql://user:pass@localhost:5432/mydb')
            >>> # 特定のテーブルのスキーマをDataFrameとして取得
            >>> schema_df = db.export_schema_to_dataframe('users')
            >>> print(schema_df)

            >>> # 全テーブルのスキーマをDataFrameとして取得
            >>> all_schemas_df = db.export_schema_to_dataframe()
            >>> print(all_schemas_df)
        """
        try:
            # テーブル名が指定されていない場合は全テーブルのスキーマを取得
            if table_name is None:
                return self.get_tables_schema()

            # 特定のテーブルのスキーマを取得
            return self.get_table_schema(table_name)

        except Exception as e:
            message = f"スキーマのDataFrame変換中にエラーが発生しました: {e}"
            print(message)
            return pd.DataFrame({"status": ["error"], "message": [message]})

    def __del__(self):
        """
        オブジェクトが破棄される際にデータベース接続を閉じる。
        デストラクタメソッド。
        """
        try:
            # 接続オブジェクトが存在する場合のみcloseを呼び出す
            if hasattr(self, "connection") and self.connection:
                self.close()
        except Exception:
            # デストラクタ内の例外は無視する
            # （プログラム終了時の安全性のため）
            pass
