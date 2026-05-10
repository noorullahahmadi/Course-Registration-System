from markupsafe import Markup, escape


class FakeLabel:
    def __init__(self, text):
        self.text = text

    def __call__(self, **attrs):
        attrs_html = "".join(
            f' {k}="{escape(v)}"' for k, v in attrs.items() if v is not None
        )
        return Markup(f"<label{attrs_html}>{escape(self.text)}</label>")


class FakeInputField:
    def __init__(self, name, label_text, input_type="text", value="", errors=None):
        self.name = name
        self.label = FakeLabel(label_text)
        self.input_type = input_type
        self.value = value
        self.errors = errors or []

    def __call__(self, **attrs):
        attrs = dict(attrs)
        if "name" not in attrs:
            attrs["name"] = self.name
        if "id" not in attrs:
            attrs["id"] = self.name
        if self.input_type != "password" and "value" not in attrs:
            attrs["value"] = self.value if self.value is not None else ""
        attrs_html = "".join(
            f' {k}="{escape(v)}"' for k, v in attrs.items() if v is not None
        )
        return Markup(f'<input type="{self.input_type}"{attrs_html}>')


class FakeCheckboxField:
    def __init__(self, name, label_text, checked=False, errors=None):
        self.name = name
        self.label = FakeLabel(label_text)
        self.checked = checked
        self.errors = errors or []

    def __call__(self, **attrs):
        attrs = dict(attrs)
        if "name" not in attrs:
            attrs["name"] = self.name
        if "id" not in attrs:
            attrs["id"] = self.name
        if "value" not in attrs:
            attrs["value"] = "1"
        checked_html = " checked" if self.checked else ""
        attrs_html = "".join(
            f' {k}="{escape(v)}"' for k, v in attrs.items() if v is not None
        )
        return Markup(f'<input type="checkbox"{checked_html}{attrs_html}>')


class FakeSubmitField:
    def __init__(self, text):
        self.text = text

    def __call__(self, **attrs):
        attrs = dict(attrs)
        if "type" not in attrs:
            attrs["type"] = "submit"
        attrs_html = "".join(
            f' {k}="{escape(v)}"' for k, v in attrs.items() if v is not None
        )
        return Markup(f"<button{attrs_html}>{escape(self.text)}</button>")


class LoginForm:
    def __init__(self):
        self.username = FakeInputField("email", "Email", input_type="email")
        self.password = FakeInputField("password", "Password", input_type="password")
        self.remember_me = FakeCheckboxField("remember_me", "Remember Me")

    def hidden_tag(self):
        return Markup("")


class RegisterForm:
    def __init__(self):
        self.full_name = FakeInputField("full_name", "Full Name")
        self.username = FakeInputField("username", "Username")
        self.email = FakeInputField("email", "Email", input_type="email")
        self.student_id = FakeInputField("student_id", "Student ID")
        self.department = FakeInputField("department", "Department")
        self.password = FakeInputField("password", "Password", input_type="password")
        self.password2 = FakeInputField("password2", "Confirm Password", input_type="password")

    def hidden_tag(self):
        return Markup("")


class StudentEditForm:
    def __init__(self, student=None):
        self.full_name = FakeInputField("full_name", "Full Name", value=getattr(student, "full_name", ""))
        self.email = FakeInputField("email", "Email", input_type="email", value=getattr(student, "email", ""))
        self.student_id = FakeInputField("student_id", "Student ID", value=getattr(student, "student_id", ""))
        self.department = FakeInputField("department", "Department", value=getattr(student, "department", ""))
        self.is_active = FakeCheckboxField("is_active", "Active Account", checked=bool(getattr(student, "is_active", 1)))
        self.submit = FakeSubmitField("Save Changes")

    def hidden_tag(self):
        return Markup("")