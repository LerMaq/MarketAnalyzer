import sys


def convert_to_raw_string():
    """
    Для преобразования обычного текста в однострочный формат.
    Необходимо для теста эндпоинта воркера POST /tasks/complete/{task_id}
    """
    print(
        "--- Вставь свой текст ниже (чтобы закончить, нажми Ctrl+D в Linux/Mac или Ctrl+Z в Windows на новой строке) ---")

    # Считываем весь введенный текст целиком
    input_data = sys.stdin.read()

    if not input_data:
        print("Текст не введен.")
        return

    # Превращаем текст в строку с явными \n
    # repr() добавит кавычки и превратит переносы в символы \n
    raw_content = repr(input_data.strip())

    print("\n--- Твой текст в формате raw (можно копировать): ---\n")
    print(raw_content)


if __name__ == "__main__":
    convert_to_raw_string()