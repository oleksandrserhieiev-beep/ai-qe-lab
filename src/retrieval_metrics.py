from constraint_filter import extract_constraints


def active_constraints(query):
    constraints = extract_constraints(query)

    return {
        key: value
        for key, value in constraints.items()
        if value is not None
    }


def _constraint_matches(product, key, expected):
    if key == "subcategory":
        return str(product.get("subcategory", "")).lower() == str(expected).lower()

    if key == "waterproof":
        return product.get("waterproof") is expected

    if key == "color":
        colors = [
            str(color).lower()
            for color in product.get("colors", [])
        ]
        return str(expected).lower() in colors

    if key == "max_price":
        price = product.get("price")
        return price is not None and float(price) <= float(expected)

    if key == "size":
        sizes = [
            str(size).upper()
            for size in product.get("sizes", [])
        ]
        return str(expected).upper() in sizes

    return False


def product_constraint_match_score(product, constraints):
    if not constraints:
        return None

    matched = sum(
        _constraint_matches(product, key, expected)
        for key, expected in constraints.items()
    )

    return round(
        matched / len(constraints) * 100,
        2,
    )


def evaluate_constraint_retrieval(query, retrieval):
    constraints = active_constraints(query)

    if not constraints:
        return {
            "applicable": False,
            "active_constraints": {},
            "constraint_match_score": None,
            "constraint_precision_at_k": None,
            "matching_products": 0,
            "retrieved_products": 0,
        }

    product_results = [
        item
        for item in retrieval
        if item.get("type") == "product"
        and item.get("metadata")
    ]

    if not product_results:
        return {
            "applicable": True,
            "active_constraints": constraints,
            "constraint_match_score": 0.0,
            "constraint_precision_at_k": 0.0,
            "matching_products": 0,
            "retrieved_products": 0,
        }

    scores = [
        product_constraint_match_score(
            item["metadata"],
            constraints,
        )
        for item in product_results
    ]

    fully_matching = sum(
        score == 100.0
        for score in scores
    )

    precision = round(
        fully_matching / len(product_results) * 100,
        2,
    )

    return {
        "applicable": True,
        "active_constraints": constraints,
        "constraint_match_score": max(scores),
        "constraint_precision_at_k": precision,
        "matching_products": fully_matching,
        "retrieved_products": len(product_results),
    }
