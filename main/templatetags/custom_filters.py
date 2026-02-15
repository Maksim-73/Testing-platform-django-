from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Вычитает arg из value (для шаблонов)"""
    return value - arg

@register.filter
def get_item(dictionary, key):
    """Получает значение по ключу из словаря"""
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """Умножает значение на аргумент"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def gte(value, arg):
    """Проверяет, больше или равно ли значение указанному аргументу."""
    try:
        return float(value) >= float(arg)
    except (ValueError, TypeError):
        return False
