"""
Googleスプレッドシートへのアクセスを提供するモジュール。

このモジュールは、Googleスプレッドシートの読み書きを簡単に行うためのクラスを提供します。
認証情報から接続を確立し、スプレッドシートのデータ操作を効率的に行うことができます。
"""

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from zangetsu_logger import initialize


class GoogleSpreadsheet:
    """
    Googleスプレッドシートへのアクセスと操作を管理するクラス。

    このクラスは、Googleスプレッドシート APIを使用してスプレッドシートの読み取り、
    書き込み、更新などの操作を行うためのメソッドを提供します。

    Args:
        credentials_path (str): Google APIの認証情報（サービスアカウントキー）へのパス。
        spreadsheet_id (str, optional): 操作対象のスプレッドシートID。

    Attributes:
        service: Googleスプレッドシート APIのサービスオブジェクト。
        spreadsheet_id (str): 現在操作中のスプレッドシートのID。

    Examples:
        # サービスアカウントキーを使用してスプレッドシートに接続
        >>> gs = GoogleSpreadsheet('/path/to/credentials.json', 'your_spreadsheet_id')
        >>> df = gs.read_sheet('Sheet1', 'A1:D10')
        >>> print(df)
    """

    def __init__(self, credentials_path: str, spreadsheet_id: str | None = None):
        """
        GoogleスプレッドシートAPIへの接続を初期化する。

        Args:
            credentials_path (str): Google APIの認証情報（サービスアカウントキー）へのパス。
            spreadsheet_id (str, optional): 操作対象のスプレッドシートID。
        """
        self.logger = initialize()

        # 認証情報の設定
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id

        # スコープの設定
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

        try:
            # サービスアカウントキーから認証情報を取得
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES
            )

            # Google Sheets APIのクライアントを作成
            self.service = build("sheets", "v4", credentials=credentials)
            self.logger.debug("Google Spreadsheet API接続を初期化しました")
        except Exception as e:
            self.logger.error(f"Google Spreadsheet API接続の初期化に失敗しました: {e}")
            raise

    def set_spreadsheet_id(self, spreadsheet_id: str) -> None:
        """
        操作対象のスプレッドシートIDを設定する。

        Args:
            spreadsheet_id (str): 設定するスプレッドシートID。

        Examples:
            >>> gs = GoogleSpreadsheet('/path/to/credentials.json')
            >>> gs.set_spreadsheet_id('your_new_spreadsheet_id')
        """
        self.spreadsheet_id = spreadsheet_id
        self.logger.debug(f"スプレッドシートID '{spreadsheet_id}' を設定しました")

    def read_sheet(
        self, sheet_name: str, range_name: str | None = None
    ) -> pd.DataFrame:
        """
        指定されたシートとセル範囲のデータをDataFrameとして読み込む。

        Args:
            sheet_name (str): 読み込むシート名。
            range_name (str, optional): 読み込むセル範囲（例: 'A1:D10'）。
                指定しない場合、シート全体を読み込む。

        Returns:
            pd.DataFrame: シートデータを含むDataFrame。

        Examples:
            >>> gs = GoogleSpreadsheet('/path/to/credentials.json', 'your_spreadsheet_id')
            >>> # 特定の範囲を読み込む
            >>> df = gs.read_sheet('Sheet1', 'A1:D10')
            >>> # シート全体を読み込む
            >>> all_data = gs.read_sheet('Sheet1')
        """
        if not self.spreadsheet_id:
            raise ValueError(
                "スプレッドシートIDが設定されていません。set_spreadsheet_id()を使用してIDを設定してください。"
            )

        try:
            # シート名とレンジを組み合わせる
            if range_name:
                full_range = f"{sheet_name}!{range_name}"
            else:
                full_range = sheet_name

            # APIリクエストを実行
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=full_range)
                .execute()
            )

            # 取得したデータを確認
            values = result.get("values", [])

            if not values:
                self.logger.warning(
                    f"シート '{sheet_name}' にデータが見つかりませんでした"
                )
                return pd.DataFrame()

            # 最初の行をヘッダーとして使用してDataFrameを作成
            header = values[0]
            data = values[1:] if len(values) > 1 else []

            # データ行の長さがヘッダーよりも短い場合、Noneで埋める
            for row in data:
                if len(row) < len(header):
                    row.extend([None] * (len(header) - len(row)))

            return pd.DataFrame(data, columns=header)

        except HttpError as error:
            self.logger.error(f"APIリクエスト中にエラーが発生しました: {error}")
            return pd.DataFrame({"error": [str(error)]})
        except Exception as e:
            self.logger.error(f"シートの読み込み中にエラーが発生しました: {e}")
            return pd.DataFrame({"error": [str(e)]})

    def write_sheet(
        self,
        df: pd.DataFrame,
        sheet_name: str,
        range_start: str = "A1",
        include_header: bool = True,
    ) -> bool:
        """
        DataFrameのデータを指定したシートの指定した位置に書き込む。

        Args:
            df (pd.DataFrame): 書き込むデータを含むDataFrame。
            sheet_name (str): 書き込み先のシート名。
            range_start (str, optional): 書き込みを開始するセル位置（例: 'A1'）。デフォルトは 'A1'。
            include_header (bool, optional): 列名をヘッダーとして含めるかどうか。デフォルトはTrue。

        Returns:
            bool: 書き込みが成功した場合はTrue、失敗した場合はFalse。

        Examples:
            >>> gs = GoogleSpreadsheet('/path/to/credentials.json', 'your_spreadsheet_id')
            >>> df = pd.DataFrame({'Name': ['Alice', 'Bob'], 'Age': [25, 30]})
            >>> gs.write_sheet(df, 'Sheet1', 'B2', include_header=True)
        """
        if not self.spreadsheet_id:
            raise ValueError(
                "スプレッドシートIDが設定されていません。set_spreadsheet_id()を使用してIDを設定してください。"
            )

        try:
            # 書き込み範囲を設定
            range_name = f"{sheet_name}!{range_start}"

            # DataFrameをリストに変換
            values = []

            # ヘッダーを含める場合
            if include_header:
                values.append(df.columns.tolist())

            # データ行を追加
            for _, row in df.iterrows():
                values.append(row.tolist())

            body = {"values": values}

            # APIリクエストを実行
            result = (
                self.service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
                .execute()
            )

            self.logger.debug(f"{result.get('updatedCells')} セルが更新されました")
            return True

        except HttpError as error:
            self.logger.error(f"APIリクエスト中にエラーが発生しました: {error}")
            return False
        except Exception as e:
            self.logger.error(f"シートへの書き込み中にエラーが発生しました: {e}")
            return False

    def append_sheet(
        self, df: pd.DataFrame, sheet_name: str, include_header: bool = False
    ) -> bool:
        """
        DataFrameのデータを指定したシートの最後に追加する。

        Args:
            df (pd.DataFrame): 追加するデータを含むDataFrame。
            sheet_name (str): 追加先のシート名。
            include_header (bool, optional): 列名をヘッダーとして含めるかどうか。デフォルトはFalse。

        Returns:
            bool: 追加が成功した場合はTrue、失敗した場合はFalse。

        Examples:
            >>> gs = GoogleSpreadsheet('/path/to/credentials.json', 'your_spreadsheet_id')
            >>> df = pd.DataFrame({'Name': ['Charlie', 'Dave'], 'Age': [35, 40]})
            >>> gs.append_sheet(df, 'Sheet1')
        """
        if not self.spreadsheet_id:
            raise ValueError(
                "スプレッドシートIDが設定されていません。set_spreadsheet_id()を使用してIDを設定してください。"
            )

        try:
            # DataFrameをリストに変換
            values = []

            # ヘッダーを含める場合
            if include_header:
                values.append(df.columns.tolist())

            # データ行を追加
            for _, row in df.iterrows():
                values.append(row.tolist())

            body = {"values": values}

            # APIリクエストを実行
            result = (
                self.service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=self.spreadsheet_id,
                    range=sheet_name,
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body=body,
                )
                .execute()
            )

            self.logger.debug(
                f"{result.get('updates').get('updatedCells')} セルが追加されました"
            )
            return True

        except HttpError as error:
            self.logger.error(f"APIリクエスト中にエラーが発生しました: {error}")
            return False
        except Exception as e:
            self.logger.error(f"シートへのデータ追加中にエラーが発生しました: {e}")
            return False

    def clear_sheet(self, sheet_name: str, range_name: str | None = None) -> bool:
        """
        指定したシートまたは範囲のデータをクリアする。

        Args:
            sheet_name (str): クリアするシート名。
            range_name (str, optional): クリアするセル範囲（例: 'A1:D10'）。
                指定しない場合、シート全体をクリアする。

        Returns:
            bool: クリアが成功した場合はTrue、失敗した場合はFalse。

        Examples:
            >>> gs = GoogleSpreadsheet('/path/to/credentials.json', 'your_spreadsheet_id')
            >>> # 特定の範囲をクリア
            >>> gs.clear_sheet('Sheet1', 'A2:D10')
            >>> # シート全体をクリア
            >>> gs.clear_sheet('Sheet1')
        """
        if not self.spreadsheet_id:
            raise ValueError(
                "スプレッドシートIDが設定されていません。set_spreadsheet_id()を使用してIDを設定してください。"
            )

        try:
            # シート名とレンジを組み合わせる
            if range_name:
                full_range = f"{sheet_name}!{range_name}"
            else:
                full_range = sheet_name

            # APIリクエストを実行
            result = (
                self.service.spreadsheets()
                .values()
                .clear(spreadsheetId=self.spreadsheet_id, range=full_range)
                .execute()
            )

            self.logger.debug(f"シート '{sheet_name}' のデータがクリアされました")
            return True

        except HttpError as error:
            self.logger.error(f"APIリクエスト中にエラーが発生しました: {error}")
            return False
        except Exception as e:
            self.logger.error(f"シートのクリア中にエラーが発生しました: {e}")
            return False

    def get_sheet_names(self) -> list[str]:
        """
        スプレッドシート内の全シート名のリストを取得する。

        Returns:
            List[str]: シート名のリスト。エラー時は空のリストを返す。

        Examples:
            >>> gs = GoogleSpreadsheet('/path/to/credentials.json', 'your_spreadsheet_id')
            >>> sheet_names = gs.get_sheet_names()
            >>> print(sheet_names)
        """
        if not self.spreadsheet_id:
            raise ValueError(
                "スプレッドシートIDが設定されていません。set_spreadsheet_id()を使用してIDを設定してください。"
            )

        try:
            # スプレッドシートのメタデータを取得
            spreadsheet = (
                self.service.spreadsheets()
                .get(spreadsheetId=self.spreadsheet_id)
                .execute()
            )

            # シート名のリストを作成
            sheet_names = [
                sheet["properties"]["title"] for sheet in spreadsheet["sheets"]
            ]
            return sheet_names

        except HttpError as error:
            self.logger.error(f"APIリクエスト中にエラーが発生しました: {error}")
            return []
        except Exception as e:
            self.logger.error(f"シート名の取得中にエラーが発生しました: {e}")
            return []

    def create_sheet(self, sheet_name: str) -> bool:
        """
        新しいシートをスプレッドシートに追加する。

        Args:
            sheet_name (str): 作成するシートの名前。

        Returns:
            bool: シート作成が成功した場合はTrue、失敗した場合はFalse。

        Examples:
            >>> gs = GoogleSpreadsheet('/path/to/credentials.json', 'your_spreadsheet_id')
            >>> gs.create_sheet('New Sheet')
        """
        if not self.spreadsheet_id:
            raise ValueError(
                "スプレッドシートIDが設定されていません。set_spreadsheet_id()を使用してIDを設定してください。"
            )

        try:
            # 新しいシートを追加するリクエストを作成
            request_body = {
                "requests": [{"addSheet": {"properties": {"title": sheet_name}}}]
            }

            # APIリクエストを実行
            result = (
                self.service.spreadsheets()
                .batchUpdate(spreadsheetId=self.spreadsheet_id, body=request_body)
                .execute()
            )

            self.logger.debug(f"新しいシート '{sheet_name}' が作成されました")
            return True

        except HttpError as error:
            if "already exists" in str(error):
                self.logger.warning(f"シート '{sheet_name}' は既に存在します")
            else:
                self.logger.error(f"APIリクエスト中にエラーが発生しました: {error}")
            return False
        except Exception as e:
            self.logger.error(f"シートの作成中にエラーが発生しました: {e}")
            return False

    def delete_sheet(self, sheet_name: str) -> bool:
        """
        指定されたシートをスプレッドシートから削除する。

        Args:
            sheet_name (str): 削除するシートの名前。

        Returns:
            bool: シート削除が成功した場合はTrue、失敗した場合はFalse。

        Examples:
            >>> gs = GoogleSpreadsheet('/path/to/credentials.json', 'your_spreadsheet_id')
            >>> gs.delete_sheet('Old Sheet')
        """
        if not self.spreadsheet_id:
            raise ValueError(
                "スプレッドシートIDが設定されていません。set_spreadsheet_id()を使用してIDを設定してください。"
            )

        try:
            # まずシートIDを見つける
            spreadsheet = (
                self.service.spreadsheets()
                .get(spreadsheetId=self.spreadsheet_id)
                .execute()
            )

            sheet_id = None
            for sheet in spreadsheet["sheets"]:
                if sheet["properties"]["title"] == sheet_name:
                    sheet_id = sheet["properties"]["sheetId"]
                    break

            if sheet_id is None:
                self.logger.warning(f"シート '{sheet_name}' が見つかりません")
                return False

            # シートを削除するリクエストを作成
            request_body = {"requests": [{"deleteSheet": {"sheetId": sheet_id}}]}

            # APIリクエストを実行
            result = (
                self.service.spreadsheets()
                .batchUpdate(spreadsheetId=self.spreadsheet_id, body=request_body)
                .execute()
            )

            self.logger.debug(f"シート '{sheet_name}' が削除されました")
            return True

        except HttpError as error:
            self.logger.error(f"APIリクエスト中にエラーが発生しました: {error}")
            return False
        except Exception as e:
            self.logger.error(f"シートの削除中にエラーが発生しました: {e}")
            return False

    def create_spreadsheet(
        self, title: str, sheet_names: list[str] = ["Sheet1"]
    ) -> str | None:
        """
        新しいスプレッドシートを作成する。

        Args:
            title (str): 作成するスプレッドシートのタイトル。
            sheet_names (List[str], optional): 作成する初期シート名のリスト。デフォルトは ['Sheet1']。

        Returns:
            Optional[str]: 作成されたスプレッドシートのID。失敗時はNone。

        Examples:
            >>> gs = GoogleSpreadsheet('/path/to/credentials.json')
            >>> new_id = gs.create_spreadsheet('My New Spreadsheet', ['Data', 'Summary', 'Charts'])
            >>> gs.set_spreadsheet_id(new_id)
        """
        try:
            # 新しいスプレッドシートのシート定義
            sheets = []
            for i, name in enumerate(sheet_names):
                # 最初のシート以外は新規に追加する必要がある
                if i > 0:
                    sheets.append({"addSheet": {"properties": {"title": name}}})

            # スプレッドシートのメタデータ
            spreadsheet_body = {"properties": {"title": title}}

            # 最初のシートの名前を設定（デフォルトのSheet1を変更）
            if sheet_names:
                spreadsheet_body["sheets"] = [{"properties": {"title": sheet_names[0]}}]

            # 新しいスプレッドシートを作成
            spreadsheet = (
                self.service.spreadsheets().create(body=spreadsheet_body).execute()
            )

            new_spreadsheet_id = spreadsheet["spreadsheetId"]

            # 追加のシートがある場合は作成
            if len(sheets) > 0:
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=new_spreadsheet_id, body={"requests": sheets}
                ).execute()

            self.logger.debug(
                f"新しいスプレッドシート '{title}' (ID: {new_spreadsheet_id}) が作成されました"
            )
            return new_spreadsheet_id

        except HttpError as error:
            self.logger.error(f"APIリクエスト中にエラーが発生しました: {error}")
            return None
        except Exception as e:
            self.logger.error(f"スプレッドシートの作成中にエラーが発生しました: {e}")
            return None

    def __str__(self) -> str:
        """
        オブジェクトの文字列表現を返す。

        Returns:
            str: オブジェクトの文字列表現。
        """
        return f"GoogleSpreadsheet(credentials_path='{self.credentials_path}', spreadsheet_id='{self.spreadsheet_id}')"
