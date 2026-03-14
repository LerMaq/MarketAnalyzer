import re


def extract_ozon_id(input_str: str) -> int:
    # Ищем цифры в ссылке (артикул обычно 9-10 цифр)
    # Пример: https://www.ozon.ru/product/naushniki-123456789/

    input_str = input_str.strip()
    if input_str.isdigit():
        return int(input_str)
    match = re.search(r"[-/](\d+)(?:/?\?|/?$)", input_str)

    if match:
        return int(match.group(1))

    raise ValueError("Не удалось извлечь артикул")
