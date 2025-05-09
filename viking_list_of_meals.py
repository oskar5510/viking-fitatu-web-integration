import csv
import logging

from collections import Counter
from typing import List, Dict

from viking_fitatu_integration import VikingClient, APIConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CSV_FILENAME = "meal_counts.csv"

def get_order_ids() -> List[str]:
    """Fetch order IDs from the Viking API."""
    try:
        response = VikingClient.get(APIConfig.VIKING_ORDER_LIST)
        return [order["orderId"] for order in response]
    except Exception as e:
        logging.error(f"Error fetching order IDs: {e}")
        return []

def get_order_data(order_id: str) -> Dict:
    """Fetch order details by order ID."""
    try:
        return VikingClient.get(APIConfig.VIKING_ORDER_URL.format(id=order_id))
    except Exception as e:
        logging.error(f"Error fetching data for order {order_id}: {e}")
        return {}

def get_meals_from_delivery(delivery_id: str) -> List[str]:
    """Fetch meal names from a specific delivery."""
    try:
        meal_details = VikingClient.get(APIConfig.VIKING_DATE_DETAILS_URL.format(id=delivery_id))
        return [meal.get("menuMealName") for meal in meal_details.get("deliveryMenuMeal", []) if
                meal.get("menuMealName")]
    except Exception as e:
        logging.error(f"Error fetching meal details for delivery {delivery_id}: {e}")
        return []

def process_order(order_id: str, meal_counter: Counter):
    """Process a single order and update the meal counter."""
    logging.info(f"Processing order {order_id}...")
    order_data = get_order_data(order_id)
    
    if not order_data:
        logging.error(f"No data found for order {order_id}")
        return
    
    for delivery in order_data.get("deliveries", []):
        delivery_id = delivery.get("deliveryId")
        if delivery_id:
            meals = get_meals_from_delivery(delivery_id)
            meal_counter.update(meals)

def count_meals_from_orders() -> Dict[str, int]:
    """Fetches and counts occurrences of menuMealName from multiple orders."""
    meal_counter = Counter()
    order_ids = get_order_ids()
    
    if not order_ids:
        logging.warning("No orders found.")
        return {}
    
    logging.info(f"Processing {len(order_ids)} orders: {order_ids}")
    
    for order_id in order_ids:
        process_order(order_id, meal_counter)

    return dict(sorted(meal_counter.items(), key=lambda x: x[1], reverse=True))

def save_meal_counts_to_csv(meal_counts: Dict[str, int], filename: str):
    """Saves meal counts to a CSV file."""
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Meal Name", "Count"])
            writer.writerows(meal_counts.items())
        logging.info(f"Meal counts saved to {filename}")
    except Exception as e:
        logging.error(f"Error writing to CSV file {filename}: {e}")

def main():
    meal_counts = count_meals_from_orders()
    if meal_counts:
        save_meal_counts_to_csv(meal_counts, CSV_FILENAME)
    else:
        logging.warning("No meal counts to save.")

if __name__ == "__main__":
    main()
