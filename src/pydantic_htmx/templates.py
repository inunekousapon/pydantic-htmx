"""
HTMLテンプレート生成モジュール
"""

from .parser import ParsedField, FieldType


class HTMLTemplates:
    """HTML要素のテンプレートを管理するクラス"""

    # フォーム全体のテンプレート
    FORM_TEMPLATE = """<form id="{form_id}" hx-post="{action}" hx-target="{target}" hx-swap="{swap}" class="pydantic-htmx-form">
{fields}
  <div class="form-actions">
    <button type="submit">{submit_text}</button>
  </div>
</form>"""

    # 各フィールドのラッパー
    FIELD_WRAPPER = """  <div class="form-field" id="field-{name}">
    <label for="{name}">{label}{required_mark}</label>
{input}
{description}
    <div class="error-message" id="{name}-error"></div>
  </div>"""

    # 入力タイプ別テンプレート
    TEXT_INPUT = """    <input type="text" id="{name}" name="{name}" {attrs}
           hx-post="{validate_url}" hx-trigger="blur" hx-target="#{name}-error" hx-swap="innerHTML"
           hx-vals='{{"_field": "{name}"}}'>"""

    NUMBER_INPUT = """    <input type="number" id="{name}" name="{name}" {attrs}
           hx-post="{validate_url}" hx-trigger="blur" hx-target="#{name}-error" hx-swap="innerHTML"
           hx-vals='{{"_field": "{name}"}}'>"""

    DATE_INPUT = """    <input type="date" id="{name}" name="{name}" {attrs}
           hx-post="{validate_url}" hx-trigger="blur" hx-target="#{name}-error" hx-swap="innerHTML"
           hx-vals='{{"_field": "{name}"}}'>"""

    CHECKBOX_INPUT = """    <input type="checkbox" id="{name}" name="{name}" {attrs}
           hx-post="{validate_url}" hx-trigger="change" hx-target="#{name}-error" hx-swap="innerHTML"
           hx-vals='{{"_field": "{name}"}}'>"""

    SELECT_INPUT = """    <select id="{name}" name="{name}" {attrs}
            hx-post="{validate_url}" hx-trigger="change" hx-target="#{name}-error" hx-swap="innerHTML"
            hx-vals='{{"_field": "{name}"}}'>
{options}
    </select>"""

    SELECT_OPTION = """      <option value="{value}"{selected}>{label}</option>"""

    DESCRIPTION = """    <small class="field-description">{description}</small>"""


class TemplateRenderer:
    """テンプレートをレンダリングするクラス"""

    def __init__(self, validate_endpoint: str = "/validate"):
        self.validate_endpoint = validate_endpoint

    def render_form(
        self,
        fields: list[ParsedField],
        form_id: str = "pydantic-form",
        action: str = "/submit",
        target: str = "#response",
        swap: str = "innerHTML",
        submit_text: str = "送信",
    ) -> str:
        """フォーム全体をレンダリング"""
        rendered_fields = "\n".join(self.render_field(field) for field in fields)

        return HTMLTemplates.FORM_TEMPLATE.format(
            form_id=form_id,
            action=action,
            target=target,
            swap=swap,
            fields=rendered_fields,
            submit_text=submit_text,
        )

    def render_field(self, field: ParsedField) -> str:
        """個別のフィールドをレンダリング"""
        input_html = self._render_input(field)

        description = ""
        if field.description:
            description = HTMLTemplates.DESCRIPTION.format(
                description=self._escape_html(field.description)
            )

        required_mark = " <span class='required'>*</span>" if field.required else ""

        return HTMLTemplates.FIELD_WRAPPER.format(
            name=field.name,
            label=self._escape_html(field.title),
            required_mark=required_mark,
            input=input_html,
            description=description,
        )

    def _render_input(self, field: ParsedField) -> str:
        """入力要素をレンダリング"""
        validate_url = self.validate_endpoint
        attrs = self._build_attrs(field)

        if field.field_type == FieldType.SELECT:
            return self._render_select(field, validate_url, attrs)
        elif field.field_type == FieldType.CHECKBOX:
            return HTMLTemplates.CHECKBOX_INPUT.format(
                name=field.name,
                attrs=attrs,
                validate_url=validate_url,
            )
        elif field.field_type == FieldType.DATE:
            return HTMLTemplates.DATE_INPUT.format(
                name=field.name,
                attrs=attrs,
                validate_url=validate_url,
            )
        elif field.field_type in (FieldType.INTEGER, FieldType.FLOAT):
            return HTMLTemplates.NUMBER_INPUT.format(
                name=field.name,
                attrs=attrs,
                validate_url=validate_url,
            )
        else:
            return HTMLTemplates.TEXT_INPUT.format(
                name=field.name,
                attrs=attrs,
                validate_url=validate_url,
            )

    def _render_select(self, field: ParsedField, validate_url: str, attrs: str) -> str:
        """選択肢をレンダリング"""
        options_html = []

        # 空の選択肢を追加（必須でない場合）
        if not field.required:
            options_html.append(
                HTMLTemplates.SELECT_OPTION.format(
                    value="",
                    label="選択してください",
                    selected="",
                )
            )

        for option in field.options:
            selected = " selected" if field.default == option.value else ""
            options_html.append(
                HTMLTemplates.SELECT_OPTION.format(
                    value=self._escape_html(option.value),
                    label=self._escape_html(option.label),
                    selected=selected,
                )
            )

        return HTMLTemplates.SELECT_INPUT.format(
            name=field.name,
            attrs=attrs,
            validate_url=validate_url,
            options="\n".join(options_html),
        )

    def _build_attrs(self, field: ParsedField) -> str:
        """HTML属性を構築"""
        attrs: list[str] = []

        if field.required:
            attrs.append("required")

        if field.default is not None and field.field_type != FieldType.SELECT:
            if field.field_type == FieldType.CHECKBOX:
                if field.default:
                    attrs.append("checked")
            else:
                attrs.append(f'value="{self._escape_html(str(field.default))}"')

        # 文字列制約
        if field.min_length is not None:
            attrs.append(f'minlength="{field.min_length}"')
        if field.max_length is not None:
            attrs.append(f'maxlength="{field.max_length}"')

        # 数値制約
        if field.ge is not None:
            attrs.append(f'min="{field.ge}"')
        elif field.gt is not None:
            attrs.append(f'min="{field.gt + 1}"')

        if field.le is not None:
            attrs.append(f'max="{field.le}"')
        elif field.lt is not None:
            attrs.append(f'max="{field.lt - 1}"')

        # パターン
        if field.pattern is not None:
            attrs.append(f'pattern="{self._escape_html(field.pattern)}"')

        # ステップ（浮動小数点の場合）
        if field.field_type == FieldType.FLOAT:
            attrs.append('step="any"')

        # プレースホルダー
        if field.placeholder is not None:
            attrs.append(f'placeholder="{self._escape_html(field.placeholder)}"')

        return " ".join(attrs)

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
