# Viking-Fitatu-Integration

A script to integrate Viking orders with Fitatu.

## Configuration

Create a `config.py` file in the same directory as the script with the following content:

```python
TARGET_DATES = ["2025-02-14", "2025-02-15"]

# Viking
VIKING_COOKIE = "__ca__chat=tbb...; SESSION=MzI3N..."
VIKING_ORDER_ID = 0000000  # Your order ID in Viking

# Fitatu
FITATU_USER_ID = 00000000  # Your user ID in Fitatu
FITATU_SECRET = "PYRX..."
FITATU_AUTHORIZATION = "Bearer eyJ0eXAiOiJKV1..."
```

### How to Retrieve Data for Configuration File

1. **Viking Credentials:** 
   - Obtain the `VIKING_COOKIE` by inspecting your session cookies after logging into Viking.
   - Find your `VIKING_ORDER_ID` in your Viking account/order history.

![How to retrieve Viking data](img/viking.png)

2. **Fitatu Credentials:**
   - `FITATU_USER_ID` can be found in your Fitatu account settings.
   - `FITATU_SECRET` and `FITATU_AUTHORIZATION` tokens are generated from Fitatu’s API or authentication system.

![How to retrieve Fitatu data](img/fitatu.png)

## Run the Script

Execute the following command in your terminal:

```sh
python3 viking-fitatu-integration.py
```

## Expected Output

Example output when running the script:

```sh
Product "Szakszuka z jajkiem sadzonym i szczypiorkiem, chleb graham" created successfully with id 108169011
Product "Shake wiśniowo-czereśniowy" created successfully with id 108169014
Product "Pierś z kurczaka w marynacie czosnkowo-miodowej w sosie własnym z ziemniakami i surówką kopenhaską" created successfully with id 108169017
...
Diet plan created successfully for 2025-02-21
```

![Automatically created data in Fitatu](img/fitatu-target.png)


## Requirements

Ensure you have Python 3 installed and all required dependencies set up before running the script. If needed, install dependencies using:

```sh
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License.
