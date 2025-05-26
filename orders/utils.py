import random
import datetime
import string


def generate_order_number(pk):
    current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%S")
    order_number = current_datetime + str(pk)
    return order_number


def generate_order_no(length=8):
    # Generate numeric part (first digit not zero)
    number = random.choice('123456789')  # first digit
    number += ''.join(str(random.randint(0, 9)) for _ in range(length - 1))

    # Generate 2 uppercase letters
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))

    return number + letters