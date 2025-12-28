FORBIDDEN_TOKENS = {"selector=", "timeout=", "sleep"}


def lint_dsl_text(text: str) -> list[str]:
    errors: list[str] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        for token in FORBIDDEN_TOKENS:
            if token in line:
                errors.append(f"Line {idx}: forbidden token '{token}'")
    return errors
