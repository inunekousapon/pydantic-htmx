"""
HTMXバリデーション機能
Pydanticのバリデーションと連動したHTMXレスポンスを生成
"""

from typing import Any
from pydantic import BaseModel, ValidationError


class ValidationResult:
    """バリデーション結果を保持するクラス"""

    def __init__(self, is_valid: bool, error_message: str | None = None):
        self.is_valid = is_valid
        self.error_message = error_message

    def to_html(self) -> str:
        """HTML形式でエラーメッセージを返す"""
        if self.is_valid:
            return ""
        if not self.error_message:
            return ""
        return (
            f'<span class="error">{self._escape_html(self.error_message)}</span>'
        )

    @staticmethod
    def _escape_html(text: str) -> str:
        """HTMLエスケープ"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )


class HTMXValidator:
    """HTMXと連動したバリデーションを行うクラス"""

    def __init__(self, model: type[BaseModel]):
        self.model = model

    def validate_field(self, field_name: str, value: Any) -> ValidationResult:
        """単一フィールドのバリデーション"""
        if field_name not in self.model.model_fields:
            return ValidationResult(False, f"不明なフィールド: {field_name}")

        field_info = self.model.model_fields[field_name]

        # 必須チェック
        if field_info.is_required() and (value is None or value == ""):
            return ValidationResult(False, "このフィールドは必須です")

        # 空値で必須でない場合はOK
        if not field_info.is_required() and (value is None or value == ""):
            return ValidationResult(True)

        # 型変換と検証のために部分的なモデルを作成
        try:
            # 部分的なバリデーションを行う
            partial_data = {field_name: value}

            # 他の必須フィールドにダミー値を設定
            for name, info in self.model.model_fields.items():
                if name != field_name and info.is_required():
                    partial_data[name] = self._get_dummy_value(info)

            self.model.model_validate(partial_data)
            return ValidationResult(True)

        except ValidationError as e:
            # 対象フィールドのエラーのみ抽出
            for error in e.errors():
                if error["loc"] and error["loc"][0] == field_name:
                    return ValidationResult(False, self._translate_error(error))

            return ValidationResult(True)

    def validate_all(self, data: dict[str, Any]) -> dict[str, ValidationResult]:
        """全フィールドのバリデーション"""
        results: dict[str, ValidationResult] = {}

        try:
            self.model.model_validate(data)
            # すべて成功
            for field_name in self.model.model_fields:
                results[field_name] = ValidationResult(True)

        except ValidationError as e:
            # 成功したフィールドを初期化
            for field_name in self.model.model_fields:
                results[field_name] = ValidationResult(True)

            # エラーがあるフィールドを更新
            for error in e.errors():
                if error["loc"]:
                    field_name = str(error["loc"][0])
                    if field_name in results:
                        results[field_name] = ValidationResult(
                            False, self._translate_error(error)
                        )

        return results

    def validate_and_parse(
        self, data: dict[str, Any]
    ) -> tuple[BaseModel | None, dict[str, ValidationResult]]:
        """バリデーションしてパースしたモデルを返す"""
        results = self.validate_all(data)

        # すべて成功したら解析されたモデルを返す
        if all(r.is_valid for r in results.values()):
            try:
                model = self.model.model_validate(data)
                return model, results
            except ValidationError:
                pass

        return None, results

    def generate_error_response(self, results: dict[str, ValidationResult]) -> str:
        """エラーレスポンスのHTMLを生成"""
        errors = []
        for field_name, result in results.items():
            if not result.is_valid:
                errors.append(f"<li>{field_name}: {result.error_message}</li>")

        if not errors:
            return '<div class="success">入力内容に問題はありません</div>'

        return f'<div class="errors"><ul>{"".join(errors)}</ul></div>'

    def _get_dummy_value(self, field_info: Any) -> Any:
        """ダミー値を生成"""
        from datetime import date

        annotation = field_info.annotation

        if annotation is str:
            return "dummy"
        if annotation is int:
            return 0
        if annotation is float:
            return 0.0
        if annotation is bool:
            return False
        if annotation is date:
            return date.today()

        return "dummy"

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
            "string_pattern_mismatch": "パターンに一致しません",
            "greater_than_equal": f'この値は{error.get("ctx", {}).get("ge", "")}以上である必要があります',
            "less_than_equal": f'この値は{error.get("ctx", {}).get("le", "")}以下である必要があります',
            "greater_than": f'この値は{error.get("ctx", {}).get("gt", "")}より大きい必要があります',
            "less_than": f'この値は{error.get("ctx", {}).get("lt", "")}より小さい必要があります',
        }

        if error_type in translations:
            return translations[error_type]

        return error.get("msg", "入力エラーです")
