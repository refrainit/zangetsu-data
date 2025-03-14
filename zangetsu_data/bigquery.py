"""
各プロダクトのトラッキングデータを格納しているGA4（BigQuery）の接続、各種データの取得メソッドを提供するモジュール
"""

import os

from zangetsu_data import Database


class BigQuery(Database):
    def __init__(
        self,
        project_id: str,
        dataset_id: str,
        credentials_path: str | None = None,
    ):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        self.connection_string = f"bigquery://{project_id}/{dataset_id}"
        super().__init__(self.connection_string)

    def __str__(self):
        return f"BigQuery Database Connection: {self.connection_string}"
