import requests
import random
import datetime
import sys

def generate_luhn_card(bin_number, length=16):
    """Generate a Luhn-valid card number from a BIN prefix."""
    card = str(bin_number)
    while len(card) < length - 1:
        card += str(random.randint(0, 9))
    
    digits = [int(d) for d in card]
    for i in range(len(digits) - 1, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    
    total = sum(digits)
    check_digit = (10 - (total % 10)) % 10
    return card + str(check_digit)

def verify_luhn(card_number):
    """Verify a card number passes Luhn check."""
    digits = [int(d) for d in card_number]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    return sum(digits) % 10 == 0

def get_random_user():
    """Fetch random identity data from randomuser.me"""
    response = requests.get("https://randomuser.me/api/")
    user = response.json()["results"][0]
    return {
        "name": f"{user['name']['first']} {user['name']['last']}",
        "email": user["email"],
        "address": f"{str(user['location']['street']['number'])} {user['location']['street']['name']}",
        "city": user["location"]["city"],
        "state": user["location"]["state"],
        "postcode": str(user["location"]["postcode"]),
        "country": user["location"]["country"]
    }

def get_card_details(bin_number):
    """Generate full card details from BIN."""
    card_number = generate_luhn_card(bin_number)
    month = str(random.randint(1, 12)).zfill(2)
    year = str(datetime.datetime.now().year + random.randint(1, 6))
    cvv = str(random.randint(100, 999))
    return card_number, month, year, cvv

if __name__ == "__main__":
    bin_input = sys.argv[1] if len(sys.argv) > 1 else "6233586370"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    for i in range(count):
        cc, mm, yy, cvv = get_card_details(bin_input)
        user = get_random_user()
        luhn_valid = verify_luhn(cc)
        
        print("=" * 50)
        print(f"BIN: {bin_input}")
        print(f"Card: {cc}")
        print(f"Exp: {mm}/{yy[-2:]}")
        print(f"CVV: {cvv}")
        print(f"Luhn Valid: {luhn_valid}")
        print("-" * 50)
        print(f"Name: {user['name']}")
        print(f"Email: {user['email']}")
        print(f"Address: {user['address']}")
        print(f"City: {user['city']}, {user['state']} {user['postcode']}")
        print(f"Country: {user['country']}")
        print("=" * 50)
        print()
