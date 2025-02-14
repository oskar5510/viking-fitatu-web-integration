import requests
import uuid
from config import TARGET_DATES, VIKING_COOKIE, VIKING_ORDER_ID, FIATU_SECRET, FIATU_AUTHORIZATION, FIATU_USER_ID
from datetime import datetime

BRAND = "Viking"

viking_headers = {"Cookie": VIKING_COOKIE}
fiatu_headers = {
    "Api-Key": "FITATU-MOBILE-APP",
    "Api-Secret": FIATU_SECRET,
    "Authorization": FIATU_AUTHORIZATION,
    "Content-Type": "application/json"
}

viking_order_url = "https://panel.kuchniavikinga.pl/api/company/customer/order/{id}"
viking_date_details_url = "https://panel.kuchniavikinga.pl/api/company/general/menus/delivery/{id}/new"
fiatu_create_product_url = "https://pl-pl.fitatu.com/api/products"
fiatu_search_product_url = "https://pl-pl.fitatu.com/api/search/food/user/{id}?date={date}&phrase={phrase}&page=1&limit=1"
fiatu_diet_plan_url = "https://pl-pl.fitatu.com/api/diet-plan/{id}/days"

def fetch_data(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data from {url}: {response.status_code} - {response.text}")
        return None

def search_product(name, date):
    url = fiatu_search_product_url.format(id=FIATU_USER_ID, date=date, phrase=name)
    response = requests.get(url, headers=fiatu_headers)
    if response.status_code == 200:
        products = response.json()
        for product in products:
            if product.get("name") == name and product.get("brand") == BRAND:
                product_id = product.get("foodId")
                print(f"Product \"{name}\" found in database successfully with id {product_id}")
                return product_id
    else:
        print(f"Error searching for product \"{name}\" on {date}: {response.status_code} - {response.text}")
    return None

def create_product(product_data):
    response = requests.post(fiatu_create_product_url, json=product_data, headers=fiatu_headers)
    if response.status_code == 201:
        return response.json().get("id")
    else:
        print(f"Error creating product: {response.status_code} - {response.text}")
    return None

def add_meal(diet_plan, meal_name, meal_id, meal_weight):
    if meal_id:
        meal_name_mapping = {
            "Śniadanie": "breakfast",
            "II śniadanie": "second_breakfast",
            "Obiad": "dinner",
            "Podwieczorek": "snack",
            "Kolacja": "supper"
        }
        if meal_name not in meal_name_mapping:
            raise ValueError(f"Meal name '{meal_name}' not found in translation map")
        diet_plan[meal_name_mapping[meal_name]] = {"items": [{
            "planDayDietItemId": str(uuid.uuid1()),
            "foodType": "PRODUCT",
            "measureId": 1,
            "measureQuantity": int(meal_weight),
            "productId": meal_id,
            "source": "API",
            "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }]}

def process_date(target_date, data):
    deliveries_on_date = [d for d in data.get("deliveries", []) if d.get("date") == target_date]
    if not deliveries_on_date:
        print(f"No deliveries found for {target_date}")
        return
    
    for delivery in deliveries_on_date:
        delivery_id = delivery["deliveryId"]
        date_data = fetch_data(viking_date_details_url.format(id=delivery_id), viking_headers)
        if not date_data:
            print(f"Failed to retrieve delivery details for {delivery_id}")
            continue
        
        meal_ids = {}
        meal_weights = {}
        for meal in date_data.get("deliveryMenuMeal", []):
            meal_name = meal.get("mealName", "")
            menu_meal_name = meal.get("menuMealName", "")
            nutrition = meal.get("nutrition", {})
            weight = nutrition.get("weight", "N/A")

            product_id = search_product(menu_meal_name, target_date)
            if not product_id:
                product_data = {
                    "name": menu_meal_name,
                    "brand": BRAND,
                    "energy": nutrition.get("calories", "N/A"),
                    "carbohydrate": nutrition.get("carbohydrate", "N/A"),
                    "sugars": nutrition.get("sugar", "N/A"),
                    "fat": nutrition.get("fat", "N/A"),
                    "protein": nutrition.get("protein", "N/A"),
                    "saturatedFat": nutrition.get("saturatedFattyAcids", "N/A"),
                    "fiber": nutrition.get("dietaryFiber", "N/A"),
                    "measures": [{"measureKey": "PACKAGE", "measureUnit": "g", "weight": str(weight)}],
                    "salt": nutrition.get("salt", "N/A")
                }
                product_id = create_product(product_data)
                print(f"Product \"{menu_meal_name}\" created successfully with id {product_id}")

            if product_id:
                meal_ids[meal_name] = product_id
                meal_weights[meal_name] = weight
            else:
                print(f"Failed to create product for \"{menu_meal_name}\"")

        diet_body = {target_date: {"dietPlan": {}}}
        for meal_name, meal_id in meal_ids.items():
            add_meal(diet_body[target_date]["dietPlan"], meal_name, meal_id, meal_weights.get(meal_name, 100))

        diet_plan_response = requests.post(fiatu_diet_plan_url.format(id=FIATU_USER_ID), json=diet_body, headers=fiatu_headers)
        if diet_plan_response.status_code == 202:
            print(f"Diet plan created successfully for {target_date}")
        else:
            print(f"Failed to create diet plan for {target_date}: {diet_plan_response.status_code} - {diet_plan_response.text}")

def main():
    order_data = fetch_data(viking_order_url.format(id=VIKING_ORDER_ID), viking_headers)
    if not order_data:
        print("Failed to retrieve orders")
        return
    
    for target_date in TARGET_DATES:
        process_date(target_date, order_data)

if __name__ == "__main__":
    main()
