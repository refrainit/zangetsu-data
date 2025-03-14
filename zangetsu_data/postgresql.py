"""
データ分析用DBとの接続を行うモジュール。

このモジュールは、特定のデータベースへの接続を管理するクラスを提供します。
設定ファイルから接続情報を取得し、データベース接続を簡易化します。
また、SQLクエリをファイルとして管理し、Jinja2テンプレートエンジンを活用します。
"""

from zangetsu_logger import initialize

from .common_database import Database


class Postgresql(Database):
    """
    データベース接続を管理するクラス。

    共通のDatabaseクラスを継承し、設定ファイルから接続情報を読み取り、
    PostgreSQLデータベースへの接続を確立します。
    また、特定の業務に特化したデータ取得メソッドを提供します。

    Args:
        host (str): データベースホスト。
        port (str): データベース接続ポート。
        db_name (str): データベース名。
        username (str): データベース接続ユーザー名。
        password (str): データベース接続パスワード。
        sql_dir (str, optional): SQLクエリファイルが格納されているディレクトリパス。
            相対パスの場合は呼び出し元のディレクトリからの相対パス、
            絶対パスの場合はそのパスをそのまま使用します。
            デフォルトは 'sql' です。

    Attributes:
        connection_string (str): データベース接続文字列。

    Examples:
        # デフォルト設定でデータベースに接続
        >>> db = Postgresql(
        ...     host='localhost',
        ...     port='5432',
        ...     db_name='mydb',
        ...     username='user',
        ...     password='pass'
        ... )
        >>> db.list_tables()

        # カスタムSQLディレクトリを指定してデータベースに接続
        >>> custom_db = Postgresql(
        ...     host='custom.host.com',
        ...     port='5433',
        ...     db_name='custom_db',
        ...     username='custom_user',
        ...     password='custom_pass',
        ...     sql_dir='/absolute/path/to/sql/files'
        ... )
    """

    def __init__(
        self,
        host: str,
        port: str,
        db_name: str,
        username: str,
        password: str,
        sql_dir: str = "sql",
    ):
        """
        データベースへの接続を初期化する。

        設定ファイルから取得した接続情報を使用して、データベース接続文字列を生成し、
        親クラスのコンストラクタを呼び出します。接続を自動的に確立します。

        Args:
            host (str): データベースホスト。
            port (str): データベース接続ポート。
            db_name (str): データベース名。
            username (str): データベース接続ユーザー名。
            password (str): データベース接続パスワード。
            sql_dir (str, optional): SQLクエリファイルが格納されているディレクトリパス。
                相対パスの場合は呼び出し元のディレクトリからの相対パス、
                絶対パスの場合はそのパスをそのまま使用します。
                デフォルトは 'sql' です。
        """
        self.logger = initialize()
        # 接続文字列を生成
        connection_string = (
            f"postgresql://{username}:{password}@{host}:{port}/{db_name}"
        )

        # 親クラスを初期化
        super().__init__(connection_string, sql_dir)

        # 接続を確立
        self.connect()
        self.logger.debug(f"Connected to PostgreSQL Database: {host}")

    def __str__(self) -> str:
        """
        オブジェクトの文字列表現を返す。

        Returns:
            str: オブジェクトの文字列表現。
        """
        # engine情報からユーザー名とパスワードを含まない表示を生成
        conn_info = str(self.engine.url)
        return f"PostgreSQL Database Connection: {conn_info}"
