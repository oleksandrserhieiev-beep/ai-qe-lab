import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

PRODUCTS_FILE = BASE_DIR / "data" / "products.json"
POLICIES_DIR = BASE_DIR / "policies"

APPROVED_POLICIES = [
    "delivery_policy.md",
    "payment_policy.md",
    "returns_policy.md",
    "warranty_policy.md",
]


def load_products():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def load_policies():
    policies = []

    for filename in APPROVED_POLICIES:
        path = POLICIES_DIR / filename

        with open(path, "r", encoding="utf-8") as file:
            content = file.read()

        policies.append({
            "document_id": filename,
            "source": str(path),
            "content": content,
        })

    return policies


if __name__ == "__main__":
    products = load_products()
    policies = load_policies()

    print(f"Loaded products: {len(products)}")
    print(f"Loaded policies: {len(policies)}")

    print("\nFirst product:")
    print(products[0])

    print("\nLoaded policy IDs:")
    for policy in policies:
        print(policy["document_id"])