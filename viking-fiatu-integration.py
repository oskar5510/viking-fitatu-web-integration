import requests
import uuid
from config import TARGET_DATE, VIKING_COOKIE, VIKING_ORDER_ID, FIATU_SECRET, FIATU_AUTHORIZATION

viking_headers = {
    "Cookie": VIKING_COOKIE
}
fiatu_headers = {
    "Api-Key": "FITATU-MOBILE-APP",
    "Api-Secret": FIATU_SECRET,
    "Content-Type": "application/json",
    "Authorization": FIATU_AUTHORIZATION
}

viking_order_url = "https://panel.kuchniavikinga.pl/api/company/customer/order/{id}"
viking_date_details_url = "https://panel.kuchniavikinga.pl/api/company/general/menus/delivery/{id}/new"
fiatu_create_product_url = "https://pl-pl.fitatu.com/api/products"
fiatu_proposals_product_url = "https://pl-pl.fitatu.com/api/products/{id}/proposals"
fiatu_diet_plan_url = "https://pl-pl.fitatu.com/api/diet-plan/{id}/days"

order_response = requests.get(viking_order_url.format(id=VIKING_ORDER_ID), headers=viking_headers)

def add_meal(diet_plan, meal_name, meal_id):
    if meal_id is not None:
        diet_plan[meal_name] = {
            "items": [
                {
                    "planDayDietItemId": str(uuid.uuid1()),
                    "foodType": "PRODUCT",
                    "measureId": 2,
                    "measureQuantity": 1,
                    "productId": meal_id,
                    "source": "API"
                }
            ]
        }

if order_response.status_code == 200:
    data = order_response.json()
    deliveries_on_date = [
        delivery for delivery in data.get("deliveries", [])
        if delivery.get("date") == TARGET_DATE
    ]

    # If we found deliveries for the specific date
    if deliveries_on_date:
        for delivery in deliveries_on_date:
            delivery_id = delivery["deliveryId"]
            date_response = requests.get(viking_date_details_url.format(id=delivery_id), headers=viking_headers)

            if date_response.status_code == 200:
                date_data = date_response.json()

                breakfast_id = None
                second_breakfast_id = None
                dinner_id = None
                snack_id = None
                supper_id = None

                for meal in date_data.get("deliveryMenuMeal", []):
                    mean_name = meal.get("mealName", "")
                    menu_meal_name = meal.get("menuMealName", "")

                    nutrition = meal.get("nutrition", {})
                    weight = nutrition.get("weight", "N/A")
                    calories = nutrition.get("calories", "N/A")
                    fat = nutrition.get("fat", "N/A")
                    saturated_fatty_acids = nutrition.get("saturatedFattyAcids", "N/A")
                    carbohydrate = nutrition.get("carbohydrate", "N/A")
                    sugar = nutrition.get("sugar", "N/A")
                    dietary_fiber = nutrition.get("dietaryFiber", "N/A")
                    protein = nutrition.get("protein", "N/A")
                    salt = nutrition.get("salt", "N/A")

                    ingredients = meal.get("ingredients", [])
                    ingredient_names = [ingredient["name"] for ingredient in ingredients]

                    product_data = {
                        "name": menu_meal_name,
                        "brand": "Viking",
                        "energy": calories,
                        "carbohydrate": carbohydrate,
                        "sugars": sugar,
                        "fat": fat,
                        "protein": protein,
                        "saturatedFat": saturated_fatty_acids,
                        "fiber": dietary_fiber,
                        "measures": [
                            {
                                "measureKey": "PACKAGE",
                                "measureUnit": "g",
                                "weight": str(weight)
                            }
                        ],
                        "salt": salt
                    }

                    print(f"\nProduct Body for \n{mean_name}: {product_data}")
                    product_response = requests.post(fiatu_create_product_url, json=product_data, headers=fiatu_headers)

                    if product_response.status_code == 201:
                        product_id = product_response.json().get("id")
                        print(f"Product created successfully with ID: {product_id}")
                        if mean_name == "Śniadanie":
                            breakfast_id = product_id
                        elif mean_name == "II śniadanie":
                            second_breakfast_id = product_id
                        elif mean_name == "Obiad":
                            dinner_id = product_id
                        elif mean_name == "Podwieczorek":
                            snack_id = product_id
                        elif mean_name == "Kolacja":
                            supper_id = product_id
                        else:
                            print(f"Unsupported meal {mean_name}. It will be not added to diet plan!")
                    else:
                        print(f"Failed to create product: {product_response.status_code}")
                        print(product_response.text)

                # diet plan

                diet_body_for_target_date = {
                    f"{TARGET_DATE}": {
                        "dietPlan": {}
                    }
                }
                add_meal(diet_body_for_target_date[f"{TARGET_DATE}"]["dietPlan"], "breakfast", breakfast_id)
                add_meal(diet_body_for_target_date[f"{TARGET_DATE}"]["dietPlan"], "second_breakfast", second_breakfast_id)
                add_meal(diet_body_for_target_date[f"{TARGET_DATE}"]["dietPlan"], "dinner", dinner_id)
                add_meal(diet_body_for_target_date[f"{TARGET_DATE}"]["dietPlan"], "snack", snack_id)
                add_meal(diet_body_for_target_date[f"{TARGET_DATE}"]["dietPlan"], "supper", supper_id)
                print(f"\nFiatu Diet Plan Body: {diet_body_for_target_date}\n")

                diet_plan_response = requests.post(fiatu_diet_plan_url.format(id=FIATU_USER_ID), json=diet_body_for_target_date, headers=fiatu_headers)

                if diet_plan_response.status_code == 202:
                    print(f"Diet plan created successfully for date {TARGET_DATE}")
                else:
                    print(f"Failed to create diet plan: {diet_plan_response.status_code}")
                    print(diet_plan_response.text)
            else:
                print(f"Failed to retrieve delivery details for {delivery_id}: {date_response.status_code}")
    else:
        print(f"No deliveries found for {TARGET_DATE}")
else:
    print("Failed to retrieve orders:", order_response.status_code)