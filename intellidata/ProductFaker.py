import csv
import random
from time import time
from decimal import Decimal
from faker import Faker

RECORD_COUNT = 1000
fake = Faker()


def create_csv_file():
    with open('/Documents/PYTHON/PROJECTS/Docs/products.csv', 'w', newline='') as csvfile:
        fieldnames = ['productid', 'name', 'type', 'coverage_limit', 'price_per_1000_units','product_date', 'description', 'photo', 'creator', 'likesports', 'liketheatre','likeconcerts','likejazz','likeclassical','likeopera','likerock','likevegas'
,'likebroadway','likemusicals']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for i in range(RECORD_COUNT):
            writer.writerow(
                {
                    'userid': fake.ean8(),
                    'username': fake.user_name(),
                    'firstname': fake.first_name(),
                    'lastname': fake.last_name(),
                    'city': fake.city(),
                    'state': fake.state_abbr(),
                    'email': fake.email(),
                    'phone': fake.phone_number(),
                    'cardno': fake.credit_card_number(card_type=None),
                    'likesports': fake.null_boolean(),
                    'liketheatre': fake.null_boolean(),
                    'likeconcerts': fake.null_boolean(),
                    'likejazz': fake.null_boolean(),
                    'likeclassical': fake.null_boolean(),
                    'likeopera': fake.null_boolean(),
                    'likerock': fake.null_boolean(),
                    'likevegas': fake.null_boolean(),
                    'likebroadway': fake.null_boolean(),
                    'likemusicals': fake.null_boolean(),
                }
            )

if __name__ == '__main__':
    create_csv_file()
