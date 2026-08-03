"""
Константы приложения users.
"""

ROLE_CUSTOMER = "customer"
ROLE_CONSULTANT = "consultant"
ROLE_MANAGER = "manager"
ROLE_ADMIN = "admin"


ROLE_CHOICES = [
    (ROLE_CUSTOMER, "Покупатель"),
    (ROLE_CONSULTANT, "Консультант"),
    (ROLE_MANAGER, "Менеджер"),
    (ROLE_ADMIN, "Администратор"),
]