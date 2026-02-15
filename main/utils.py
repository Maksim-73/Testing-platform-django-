# main/utils.py
import random
import string


def generate_unique_code():
    from main.models import Test  # Импортируем модель локально

    for _ in range(100):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        if not Test.objects.filter(code=code).exists():
            return code
    raise Exception("Не удалось сгенерировать уникальный код теста.")
