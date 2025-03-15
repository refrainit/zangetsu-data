"""Databaseクラスのユニットテスト"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from zangetsu_data.common_database import Database


class TestDatabase:
    """Databaseクラスのテスト"""

    @pytest.fixture
    def db(self, mock_database_engine):
        """テスト用のDatabaseインスタンスを作成"""
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("jinja2.FileSystemLoader") as mock_loader:
                db = Database("sqlite:///:memory:", "test_sql")
                return db

    def test_init(self, db, mock_database_engine):
        """初期化が正しく行われることをテスト"""
        assert db.engine == mock_database_engine.return_value
        assert db.connection is None
        assert db.jinja_env is not None

    def test_connect(self, db):
        """connect()メソッドが正しく動作することをテスト"""
        db.connect()
        assert db.connection is not None
        assert db.connection == db.engine.connect.return_value

    def test_close(self, db):
        """close()メソッドが正しく動作することをテスト"""
        # 接続をセットアップ
        db.connection = MagicMock()
        connection = db.connection  # 接続オブジェクトの参照を保存

        # closeメソッドを呼び出し
        db.close()

        # 接続が閉じられたことを確認
        connection.close.assert_called_once()  # 保存した参照で検証
        assert db.connection is None

    def test_show_database_info(self, db):
        """show_database_info()メソッドが正しく動作することをテスト"""
        db.engine = MagicMock()
        db.engine.__str__.return_value = "mock_db_info"

        result = db.show_database_info()

        assert isinstance(result, pd.DataFrame)
        assert result["database_info"].iloc[0] == "mock_db_info"

    def test_read_sql(self, db):
        """read_sql()メソッドが正しく動作することをテスト"""
        with patch("pandas.read_sql_query") as mock_read_sql:
            mock_df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
            mock_read_sql.return_value = mock_df

            # パラメータなしでクエリ実行
            result1 = db.read_sql("SELECT * FROM table")
            mock_read_sql.assert_called_with("SELECT * FROM table", db.engine)
            assert result1.equals(mock_df)

            # パラメータありでクエリ実行
            result2 = db.read_sql("SELECT * FROM table WHERE id = %s", [1])
            mock_read_sql.assert_called_with(
                "SELECT * FROM table WHERE id = %s", db.engine, params=[1]
            )
            assert result2.equals(mock_df)

    def test_list_tables(self, db):
        """list_tables()メソッドが正しく動作することをテスト"""
        with patch("sqlalchemy.inspect") as mock_inspect:
            inspector = MagicMock()
            mock_inspect.return_value = inspector
            inspector.get_table_names.return_value = ["table1", "table2"]

            result = db.list_tables()

            assert isinstance(result, pd.DataFrame)
            assert result["table_name"].tolist() == ["table1", "table2"]
            inspector.get_table_names.assert_called_once()

    def test_get_query_from_file(self, db):
        """get_query_from_file()メソッドが正しく動作することをテスト"""
        # モックテンプレート作成
        mock_template = MagicMock()
        mock_template.render.return_value = (
            "SELECT * FROM users WHERE age > {{min_age}}"
        )

        db.jinja_env = MagicMock()
        db.jinja_env.get_template.return_value = mock_template

        result = db.get_query_from_file("query_name", min_age=18)

        # テンプレート取得とレンダリングが正しく呼び出されたか確認
        db.jinja_env.get_template.assert_called_with("query_name.sql")
        mock_template.render.assert_called_with(min_age=18)
        assert result == "SELECT * FROM users WHERE age > {{min_age}}"
