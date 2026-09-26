def strip_required(value: object) -> object:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be blank")
    return stripped


def strip_upper(value: object) -> object:
    stripped = strip_required(value)
    if isinstance(stripped, str):
        return stripped.upper()
    return stripped


def normalize_email(value: object) -> object:
    if isinstance(value, str):
        return value.strip().lower()
    return value
