import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_spaces(text):
    """Strip the ends and collapse repeated spaces into one."""
    return re.sub(r"\s+", " ", (text or "")).strip()


def clean_name(name):
    """'  JAMES   o'CONNOR ' -> "James O'Connor"."""
    name = clean_spaces(name).lower()
    # Capitalise the first letter after the start, a space, an apostrophe or a hyphen
    return re.sub(r"(^|[\s'\-])([^\W\d_])", lambda m: m.group(1) + m.group(2).upper(), name)


def clean_email(email):
    """'  Daniel.Okafor@Northwind.co ' -> 'daniel.okafor@northwind.co'."""
    return clean_spaces(email).lower()


def is_valid_email(email):
    return bool(EMAIL_PATTERN.match(email))


def make_email_key(email):
    """Key used for duplicate checks. Removes '+tag' so tom+x@a.com == tom@a.com."""
    local, _, domain = email.partition("@")
    local = local.split("+")[0]
    return f"{local}@{domain}"



def clean_lead(raw):
    """Take one raw form submission and return a clean version plus a list of issues."""
    issues = []

    # .get() means a missing key (like S-05 with no email) will not crash the script
    email = clean_email(raw.get("email"))
    message = clean_spaces(raw.get("message"))

    if not email:
        issues.append("missing_email")
    elif not is_valid_email(email):
        issues.append("invalid_email")

    if not message:
        issues.append("empty_message")

    return {
        "id": raw.get("id", ""),
        "received_at": clean_spaces(raw.get("received_at")),
        "name": clean_name(raw.get("name")),
        "email": email,
        "email_key": make_email_key(email) if email and "invalid_email" not in issues else "",
        "company": clean_spaces(raw.get("company")),
        "message": message,
        "issues": issues,
    }