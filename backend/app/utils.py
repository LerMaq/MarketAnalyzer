import re


def extract_ozon_id(input_str: str) -> int:
    # Ищем цифры в ссылке (артикул обычно 9-10 цифр)
    # Пример: https://www.ozon.ru/product/naushniki-123456789/
    match = re.search(r"product/.*?(\d+)", input_str)
    if match:
        return int(match.group(1))

    # Если ввели просто цифры (артикул)
    if input_str.isdigit():
        return int(input_str)

    raise ValueError("Не удалось извлечь артикул из ссылки")