from .vedmist import Stamp

def check_stamp(stamp: Stamp) -> list[str]:
    # Project contract, NOT a claimed GOST clause.
    # ПРОВЕРИТЬ ПО ТЕКСТУ ГОСТ: mandatory fields and numbering rules.
    errors = [f'EMPTY_{k}' for k, v in stamp.attributes().items() if not v.strip()]
    if stamp.sheet and (not stamp.sheet.isascii() or not stamp.sheet.isdecimal()
                        or int(stamp.sheet) < 1):
        errors.append('INVALID_SHEET')
    return errors
