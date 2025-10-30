from typing import List, Dict


def clean_products(raw_products: List[Dict]) -> List[Dict]:
    cleaned = []
    print(raw_products)
    for item in raw_products:
        name = item.get("name", "").strip()
        url = item.get("url", "").split("?")[0] if item.get("url") else None
        price = item.get("price", None)

        if name and url:
            cleaned.append({
                "name": name,
                "url": url,
                "price": price if isinstance(price, (int, float)) else None
            })
    return cleaned
