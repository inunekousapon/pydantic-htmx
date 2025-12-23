"""
メインのフォーム生成クラス
Pydanticモデルを受け取ってHTMXフォームを生成
"""

from typing import Literal
from pydantic import BaseModel

from .parser import ModelParser, ParsedField
from .templates import TemplateRenderer
from .validators import HTMXValidator


class FormGenerator:
    """PydanticモデルからHTMXフォームを生成するメインクラス"""

    def __init__(
        self,
        model: type[BaseModel],
        validate_endpoint: str = "/validate",
    ):
        """
        Args:
            model: Pydanticモデルクラス
            validate_endpoint: バリデーションエンドポイントのベースURL
        """
        self.model = model
        self.validate_endpoint = validate_endpoint
        self.fields = ModelParser.parse(model)
        self.renderer = TemplateRenderer(validate_endpoint)
        self.validator = HTMXValidator(model)

    def generate_form(
        self,
        form_id: str | None = None,
        action: str = "/submit",
        target: str = "#response",
        swap: Literal[
            "innerHTML",
            "outerHTML",
            "beforeend",
            "afterend",
            "beforebegin",
            "afterbegin",
            "delete",
            "none",
        ] = "innerHTML",
        submit_text: str = "送信",
    ) -> str:
        """
        HTMLフォームを生成

        Args:
            form_id: フォームのID（デフォルトはモデル名から生成）
            action: フォーム送信先のURL
            target: HTMXのターゲットセレクタ
            swap: HTMXのスワップ方式
            submit_text: 送信ボタンのテキスト

        Returns:
            生成されたHTMLフォーム文字列
        """
        if form_id is None:
            form_id = f"{self.model.__name__.lower()}-form"

        return self.renderer.render_form(
            fields=self.fields,
            form_id=form_id,
            action=action,
            target=target,
            swap=swap,
            submit_text=submit_text,
        )

    def generate_field(self, field_name: str) -> str:
        """
        個別のフィールドHTMLを生成

        Args:
            field_name: フィールド名

        Returns:
            生成されたHTMLフィールド文字列
        """
        for field in self.fields:
            if field.name == field_name:
                return self.renderer.render_field(field)

        raise ValueError(f"フィールドが見つかりません: {field_name}")

    def get_fields(self) -> list[ParsedField]:
        """解析されたフィールド情報を取得"""
        return self.fields

    def get_validator(self) -> HTMXValidator:
        """バリデーターを取得"""
        return self.validator

    def generate_css(self) -> str:
        """基本的なスタイルシートを生成"""
        return """<style>
.pydantic-htmx-form {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
}

.form-field {
  margin-bottom: 15px;
}

.form-field label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-field input,
.form-field select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}

.form-field input[type="checkbox"] {
  width: auto;
}

.form-field .required {
  color: red;
}

.form-field .field-description {
  display: block;
  color: #666;
  font-size: 0.9em;
  margin-top: 3px;
}

.error-message {
  min-height: 20px;
  margin-top: 3px;
}

.error-message .error {
  color: #d32f2f;
  font-size: 0.9em;
}

.error-message .valid {
  color: #388e3c;
}

.form-actions {
  margin-top: 20px;
}

.form-actions button {
  background-color: #1976d2;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.form-actions button:hover {
  background-color: #1565c0;
}

.errors {
  background-color: #ffebee;
  border: 1px solid #f44336;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 15px;
}

.errors ul {
  margin: 0;
  padding-left: 20px;
  color: #c62828;
}

.success {
  background-color: #e8f5e9;
  border: 1px solid #4caf50;
  border-radius: 4px;
  padding: 10px;
  color: #2e7d32;
}
</style>"""

    def generate_full_html(
        self,
        title: str = "フォーム",
        form_id: str | None = None,
        action: str = "/submit",
        target: str = "#response",
        submit_text: str = "送信",
        include_htmx: bool = True,
    ) -> str:
        """
        完全なHTMLドキュメントを生成

        Args:
            title: ページタイトル
            form_id: フォームのID
            action: フォーム送信先のURL
            target: HTMXのターゲットセレクタ
            submit_text: 送信ボタンのテキスト
            include_htmx: htmx.jsのCDNリンクを含めるか

        Returns:
            完全なHTMLドキュメント
        """
        htmx_script = ""
        if include_htmx:
            htmx_script = '<script src="https://unpkg.com/htmx.org@2.0.4"></script>'

        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  {htmx_script}
  {self.generate_css()}
</head>
<body>
  <h1>{title}</h1>
  {self.generate_form(form_id=form_id, action=action, target=target, submit_text=submit_text)}
  <div id="response"></div>
</body>
</html>"""
