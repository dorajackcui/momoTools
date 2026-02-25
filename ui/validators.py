class ValidationError(ValueError):
    """Raised when UI input validation fails."""


def parse_positive_int(raw_value, field_name):
    value_text = str(raw_value).strip()
    if not value_text:
        raise ValidationError(f"{field_name}不能为空")

    try:
        parsed = int(value_text)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name}必须是整数")

    if parsed <= 0:
        raise ValidationError(f"{field_name}必须大于0")

    return parsed


def parse_column_1_based_to_0_based(raw_value, field_name):
    return parse_positive_int(raw_value, field_name) - 1

