import re


def extract_constraints(query):
    query_lower = query.lower()

    constraints = {
        "subcategory": None,
        "waterproof": None,
        "color": None,
        "max_price": None,
        "size": None,
    }

    # Product type
    if "jacket" in query_lower:
        constraints["subcategory"] = "Jackets"

    # Waterproof
    if "waterproof" in query_lower:
        constraints["waterproof"] = True

    # Color
    if "black" in query_lower:
        constraints["color"] = "black"

    # Price: under $150 / under 150 dollars
    price_match = re.search(
        r"(?:under|below|less than)\s*\$?(\d+(?:\.\d+)?)",
        query_lower,
    )

    if price_match:
        constraints["max_price"] = float(
            price_match.group(1)
        )

    # Size
    size_match = re.search(
        r"\bsize\s+([a-z0-9]+)\b",
        query_lower,
    )

    if size_match:
        constraints["size"] = (
            size_match.group(1).upper()
        )

    return constraints


def product_matches_constraints(product, constraints):
    if constraints["subcategory"]:
        if (
            product["subcategory"].lower()
            != constraints["subcategory"].lower()
        ):
            return False

    if constraints["waterproof"] is not None:
        if (
            product["waterproof"]
            != constraints["waterproof"]
        ):
            return False

    if constraints["color"]:
        colors = [
            color.lower()
            for color in product["colors"]
        ]

        if constraints["color"].lower() not in colors:
            return False

    if constraints["max_price"] is not None:
        if product["price"] > constraints["max_price"]:
            return False

    if constraints["size"]:
        sizes = [
            size.upper()
            for size in product["sizes"]
        ]

        if constraints["size"].upper() not in sizes:
            return False

    return True