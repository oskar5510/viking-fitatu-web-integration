import csv
import logging

from collections import Counter
from viking_fitatu_integration import VikingClient, APIConfig

csv_filename = "meal_counts.csv"

def get_order_ids():
    response = VikingClient.get(APIConfig.VIKING_ORDER_LIST)
    return [order["orderId"] for order in response]

def count_meals_from_orders() -> dict:
    """Fetches and counts occurrences of menuMealName from multiple orders within given date ranges."""
    meal_counter = Counter()

    order_ids = get_order_ids()
    logging.info(f"Orders {order_ids}")

    for order_id in order_ids:
        print(f"Processing order {order_id}...")
        order_data = VikingClient.get(APIConfig.VIKING_ORDER_URL.format(id=order_id))
        
        if not order_data:
            logging.error(f"Failed to retrieve order {order_id}")
            continue

        for delivery in order_data.get("deliveries", []):            
            delivery_id = delivery["deliveryId"]

            meal_details = VikingClient.get(APIConfig.VIKING_DATE_DETAILS_URL.format(id=delivery_id))
            if meal_details:
                for meal in meal_details.get("deliveryMenuMeal", []):
                    meal_name = meal.get("menuMealName")
                    if meal_name:
                        meal_counter[meal_name] += 1

    return dict(sorted(meal_counter.items(), key=lambda x: x[1], reverse=True))


meal_counts = count_meals_from_orders()

with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Meal Name", "Count"]) 

    for meal, count in meal_counts.items():
        writer.writerow([meal, count])

logging.info(f"Meal counts saved to {csv_filename}")