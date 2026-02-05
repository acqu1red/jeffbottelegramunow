from dataclasses import dataclass


@dataclass(frozen=True)
class Tariff:
    code: str
    months: int
    price_stars: int
    price_rub: int


TARIFFS: dict[str, Tariff] = {
    "1m": Tariff(code="1m", months=1, price_stars=250, price_rub=100),
    "3m": Tariff(code="3m", months=3, price_stars=650, price_rub=300),
    "6m": Tariff(code="6m", months=6, price_stars=1200, price_rub=480),
    "12m": Tariff(code="12m", months=12, price_stars=2100, price_rub=780),
}


def get_tariff(code: str) -> Tariff:
    if code not in TARIFFS:
        raise ValueError("Unknown tariff")
    return TARIFFS[code]
