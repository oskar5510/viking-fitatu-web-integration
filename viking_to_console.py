import requests
import logging
import config
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BRAND = "Viking"
TARGET_DATES = getattr(config, "TARGET_DATES", None)
TARGET_DATE_RANGE = getattr(config, "TARGET_DATE_RANGE", None)

class APIConfig:
    """Stores API configurations for Viking."""
    VIKING_HEADERS = {"Cookie": config.VIKING_COOKIE}
    VIKING_ORDER_URL = "https://panel.kuchniavikinga.pl/api/company/customer/order/{id}"
    VIKING_DATE_DETAILS_URL = "https://panel.kuchniavikinga.pl/api/company/general/menus/delivery/{id}/new"

class BaseClient:
    """Base class for API clients with request handling."""
    @staticmethod
    def get(url: str, headers: dict) -> dict | None:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        logging.error(f"Error fetching data from {url}: {response.status_code} - {response.text}")
        return None

class VikingClient(BaseClient):
    """Handles API interactions with Viking."""
    @staticmethod
    def get(url: str, **kwargs) -> dict | None:
        return BaseClient.get(url, APIConfig.VIKING_HEADERS)

def select_dates() -> list[str]:
    """Selects dates based on provided config variables."""
    if TARGET_DATES and TARGET_DATE_RANGE:
        raise ValueError("Only one of TARGET_DATES or TARGET_DATE_RANGE should be provided.")
    if isinstance(TARGET_DATES, list):
        logging.info(f"Selected dates: {TARGET_DATES}")
        return TARGET_DATES
    if isinstance(TARGET_DATE_RANGE, tuple) and len(TARGET_DATE_RANGE) == 2:
        start_date, end_date = map(lambda d: datetime.strptime(d, "%Y-%m-%d"), TARGET_DATE_RANGE)
        selected_dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end_date - start_date).days + 1)]
        logging.info(f"Selected date range: {TARGET_DATE_RANGE}")
        return selected_dates
    logging.error("No valid dates provided. Skipping...")
    return []

def fetch_deliveries_for_date(data: dict, target_date: str) -> list:
    """Fetches deliveries for a specific date."""
    return [d for d in data.get("deliveries", []) if d.get("date") == target_date]

def fetch_viking_meal_details(delivery_id: str) -> dict | None:
    """Fetches detailed meal information from Viking for a specific delivery."""
    return VikingClient.get(APIConfig.VIKING_DATE_DETAILS_URL.format(id=delivery_id))

def print_meals_for_date(target_date: str, data: dict):
    """Wyświetla posiłki dla danego dnia w konsoli w formie tabeli z makroskładnikami."""
    from tabulate import tabulate
    deliveries_on_date = fetch_deliveries_for_date(data, target_date)
    if not deliveries_on_date:
        print(f"Brak posiłków dla {target_date}")
        return
    print(f"\nPosiłki na dzień: {target_date}")
    table = []
    headers = [
        "Posiłek", "Nazwa", "Waga [g]", "Kalorie [kcal]", "Białko [g]", "Tłuszcz [g]", "Węglowodany [g]", "Błonnik [g]", "Cukry [g]", "Sól [g]"
    ]
    for delivery in deliveries_on_date:
        delivery_id = delivery["deliveryId"]
        viking_date_data = fetch_viking_meal_details(delivery_id)
        if not viking_date_data:
            print(f"  Błąd pobierania szczegółów dostawy {delivery_id}")
            continue
        for meal in viking_date_data.get("deliveryMenuMeal", []):
            if meal.get("deliveryMealId") is None:
                continue
            menu_meal_name = meal.get("menuMealName")
            meal_name = meal.get("mealName")
            nutrition = meal.get("nutrition")
            weight = nutrition.get("weight")
            calories = nutrition.get("calories")
            protein = nutrition.get("protein")
            fat = nutrition.get("fat")
            carbs = nutrition.get("carbohydrate")
            fiber = nutrition.get("dietaryFiber")
            sugar = nutrition.get("sugar")
            salt = nutrition.get("salt")
            table.append([
                meal_name, menu_meal_name, weight, calories, protein, fat, carbs, fiber, sugar, salt
            ])
    if table:
        print(tabulate(table, headers=headers, tablefmt="github", numalign="right", stralign="left"))
    else:
        print("Brak posiłków do wyświetlenia.")

def main():
    """Main execution flow."""
    order_data = VikingClient.get(APIConfig.VIKING_ORDER_URL.format(id=config.VIKING_ORDER_ID))
    if not order_data:
        logging.error("Failed to retrieve orders")
        return
    for target_date in select_dates():
        print_meals_for_date(target_date, order_data)

if __name__ == "__main__":
    main()
