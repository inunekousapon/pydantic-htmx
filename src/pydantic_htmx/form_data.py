"""
フォームデータをPydanticモデルに変換するモジュール
"""

from typing import Any, get_args, get_origin
from datetime import date
from pydantic import BaseModel, ValidationError

from .parser import ModelParser, FieldType


class FormDataParser:
    """フォームデータをPydanticモデルに変換するクラス"""

    def __init__(self, model: type[BaseModel]):
        """
        Args:
            model: Pydanticモデルクラス
        """
        self.model = model
        self.fields = {f.name: f for f in ModelParser.parse(model)}

    def parse(self, form_data: dict[str, Any]) -> BaseModel:
        """
        フォームデータをPydanticモデルに変換

        Args:
            form_data: フォームから送信されたデータ（通常は文字列の辞書）

        Returns:
            パース済みのPydanticモデルインスタンス

        Raises:
            ValidationError: バリデーションエラーが発生した場合
        """
        converted_data = self._convert_form_data(form_data)
        return self.model.model_validate(converted_data)

    def parse_safe(
        self, form_data: dict[str, Any]
    ) -> tuple[BaseModel | None, dict[str, str]]:
        """
        フォームデータを安全にPydanticモデルに変換

        Args:
            form_data: フォームから送信されたデータ

        Returns:
            (モデルインスタンス or None, エラー辞書)のタプル
            成功時はモデルインスタンスと空の辞書
            失敗時はNoneとフィールド名→エラーメッセージの辞書
        """
        try:
            model = self.parse(form_data)
            return model, {}
        except ValidationError as e:
            errors: dict[str, str] = {}
            for error in e.errors():
                if error["loc"]:
                    field_name = str(error["loc"][0])
                    errors[field_name] = self._translate_error(error)
            return None, errors

    def _convert_form_data(self, form_data: dict[str, Any]) -> dict[str, Any]:
        """フォームデータを適切な型に変換"""
        converted: dict[str, Any] = {}

        for field_name, parsed_field in self.fields.items():
            if field_name not in form_data:
                # フィールドが存在しない場合
                # チェックボックスは未チェック時に送信されないためFalseとして扱う
                if parsed_field.field_type == FieldType.CHECKBOX:
                    converted[field_name] = False
                continue

            value = form_data[field_name]
            converted_value = self._convert_value(value, parsed_field)
            converted[field_name] = converted_value

        return converted

    def _convert_value(self, value: Any, parsed_field: Any) -> Any:
        """個別の値を適切な型に変換"""
        # 空文字列の処理
        if value == "" or value is None:
            if not parsed_field.required:
                return None
            return value  # Pydanticにバリデーションエラーを出させる

        field_type = parsed_field.field_type

        try:
            if field_type == FieldType.INTEGER:
                return int(value)

            elif field_type == FieldType.FLOAT:
                return float(value)

            elif field_type == FieldType.CHECKBOX or field_type == FieldType.BOOLEAN:
                # チェックボックスは "on", "true", "1" などで送信される
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ("on", "true", "1", "yes", "checked")
                return bool(value)

            elif field_type == FieldType.DATE:
                if isinstance(value, date):
                    return value
                if isinstance(value, str):
                    # ISO形式の日付文字列をパース
                    return date.fromisoformat(value)

            elif field_type == FieldType.SELECT:
                # 選択肢はそのまま文字列として返す
                return str(value)

            elif field_type == FieldType.STRING:
                return str(value)

        except (ValueError, TypeError):
            # 変換に失敗した場合は元の値を返し、Pydanticにバリデーションを任せる
            return value

        return value

    def _translate_error(self, error: dict[str, Any]) -> str:
        """Pydanticのエラーメッセージを日本語に翻訳"""
        error_type = error.get("type", "")

        translations = {
            "string_too_short": "この値は短すぎます",
            "string_too_long": "この値は長すぎます",
            "value_error": "値が無効です",
            "type_error": "型が正しくありません",
            "missing": "このフィールドは必須です",
            "int_parsing": "整数を入力してください",
            "float_parsing": "数値を入力してください",
            "bool_parsing": "真偽値を入力してください",
            "date_parsing": "有効な日付を入力してください",
            "date_from_datetime_parsing": "有効な日付を入力してください",
            "string_pattern_mismatch": "パターンに一致しません",
            "greater_than_equal": f'この値は{error.get("ctx", {}).get("ge", "")}以上である必要があります',
            "less_than_equal": f'この値は{error.get("ctx", {}).get("le", "")}以下である必要があります',
            "greater_than": f'この値は{error.get("ctx", {}).get("gt", "")}より大きい必要があります',
            "less_than": f'この値は{error.get("ctx", {}).get("lt", "")}より小さい必要があります',
        }

        if error_type in translations:
            return translations[error_type]

        return error.get("msg", "入力エラーです")


def parse_form_data(model: type[BaseModel], form_data: dict[str, Any]) -> BaseModel:
    """
    フォームデータをPydanticモデルに変換するヘルパー関数

    Args:
        model: Pydanticモデルクラス
        form_data: フォームから送信されたデータ

    Returns:
        パース済みのPydanticモデルインスタンス

    Raises:
        ValidationError: バリデーションエラーが発生した場合

    Example:
        ```python
        from pydantic import BaseModel, Field
        from pydantic_htmx import parse_form_data

        class UserForm(BaseModel):
            username: str = Field(min_length=3)
            age: int = Field(ge=18)

        # フォームデータ（通常はrequest.form等から取得）
        form_data = {"username": "john", "age": "25"}

        user = parse_form_data(UserForm, form_data)
        print(user.username)  # "john"
        print(user.age)       # 25 (int型に変換される)
        ```
    """
    parser = FormDataParser(model)
    return parser.parse(form_data)


def parse_form_data_safe(
    model: type[BaseModel], form_data: dict[str, Any]
) -> tuple[BaseModel | None, dict[str, str]]:
    """
    フォームデータを安全にPydanticモデルに変換するヘルパー関数

    Args:
        model: Pydanticモデルクラス
        form_data: フォームから送信されたデータ

    Returns:
        (モデルインスタンス or None, エラー辞書)のタプル

    Example:
        ```python
        from pydantic import BaseModel, Field
        from pydantic_htmx import parse_form_data_safe

        class UserForm(BaseModel):
            username: str = Field(min_length=3)
            age: int = Field(ge=18)

        form_data = {"username": "ab", "age": "15"}

        user, errors = parse_form_data_safe(UserForm, form_data)
        if user:
            print("成功:", user)
        else:
            print("エラー:", errors)
            # {'username': 'この値は短すぎます', 'age': 'この値は18以上である必要があります'}
        ```
    """
    parser = FormDataParser(model)
    return parser.parse_safe(form_data)
