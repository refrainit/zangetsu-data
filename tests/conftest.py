import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# テスト対象のモジュールをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# 基本的なフィクスチャの例
@pytest.fixture(scope="function")
def setup_function():
    """各テスト関数の前に実行されるセットアップ"""
    print("セットアップ処理を実行します")
    yield
    print("クリーンアップ処理を実行します")


@pytest.fixture(scope="module")
def setup_module():
    """各テストモジュールの前に実行されるセットアップ"""
    print("モジュールのセットアップを実行します")
    yield
    print("モジュールのクリーンアップを実行します")


@pytest.fixture(scope="session")
def setup_session():
    """テストセッション全体で一度だけ実行されるセットアップ"""
    print("セッションのセットアップを実行します")
    yield
    print("セッションのクリーンアップを実行します")


@pytest.fixture
def mock_database_engine():
    """SQLAlchemyエンジンをモック化するフィクスチャ"""
    with patch("sqlalchemy.create_engine") as mock_engine:
        engine = MagicMock()
        mock_engine.return_value = engine
        yield mock_engine


@pytest.fixture
def mock_spreadsheet_service():
    """Googleスプレッドシートサービスをモック化するフィクスチャ"""
    with patch("googleapiclient.discovery.build") as mock_build:
        service = MagicMock()
        mock_build.return_value = service
        yield service


@pytest.fixture
def mock_credentials():
    """Google認証情報をモック化するフィクスチャ"""
    with patch("google.oauth2.service_account.Credentials") as mock_creds:
        credentials = MagicMock()
        mock_creds.from_service_account_file.return_value = credentials
        yield credentials
