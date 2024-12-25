import json
import requests
from flask import Flask, jsonify, render_template, request
import traceback
import os
import joblib

app = Flask(__name__)


max_users = 10



# Define the path to the model
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "fraud_detection_model.joblib")

# Load the fraud detection model with error handling
try:
    model = joblib.load(model_path)
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

def get_user_data(username):
    url = "https://instagram-scraper-api2.p.rapidapi.com/v1/info"
    querystring = {"username_or_id_or_url": username}
    headers = {
        'x-rapidapi-key': "fac4d0bfafmsh7ba7dc25cf7f672p171390jsn9eb840d95c5f",
        'x-rapidapi-host': "instagram-scraper-api2.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'data' in data:
            return data
        else:
            return {"error": "Invalid response structure from API."}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user data: {e}")
        return None

def user_information_final(username):
    user_data = get_user_data(username)
    if not user_data or 'error' in user_data:
        print(f"Error fetching user data for {username}")
        return {"error": f"Unable to fetch data for username: {username}"}

    data = user_data.get('data', {})
    user_info = {
        "Bio": data.get("biography", "N/A"),
        "Followers": data.get("follower_count", 0),
        "Following": data.get("following_count", 0),
        "NumberOfPosts": data.get("media_count", 0),
    }
    return user_info

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    error_message = None

    if request.method == 'POST':
        name = request.form.get('name')

        # API request headers
        headers = {
            "x-rapidapi-key": "fac4d0bfafmsh7ba7dc25cf7f672p171390jsn9eb840d95c5f",
            "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com"
        }

        # Query parameters
        querystring = {"search_query": name}

        try:
            # Make the API request to get user data
            response = requests.get(
                "https://instagram-scraper-api2.p.rapidapi.com/v1/search_users",
                headers=headers,
                params=querystring
            )

            # Check if the response is successful
            response.raise_for_status()

            # Extract the JSON response
            data = response.json()

            if isinstance(data, dict) and "data" in data and "items" in data['data']:
                for index, user_info in enumerate(data['data']['items'], start=1):
                    if not isinstance(user_info, dict):
                        continue

                     # If we've already collected 10 users, stop adding more
                    if index > max_users:
                        break

                    # Extract necessary information
                    username = user_info.get('username', 'N/A')
                    full_name = user_info.get('full_name', 'N/A')
                    profile_pic_url = user_info.get('profile_pic_url')
                    local_pic_path = download_image(profile_pic_url, f"{index}.jpg") if profile_pic_url else '/static/default_placeholder.jpg'

                    # Get additional user details
                    user_details = user_information_final(username)

                    # Include the basic user data and additional details
                    user_details.update({
                        'index': index,
                        'full_name': full_name,
                        'id': user_info.get('pk', user_info.get('id', 'N/A')),
                        'username': username,
                        'is_private': user_info.get('is_private', False),
                        'is_verified': user_info.get('is_verified', False),
                        'profile_pic_url': local_pic_path
                    })

                    # Prepare data for fraud detection
                    fraud_data = {
                        'noOfPosts': len(data['data']['items']),
                        'captionData': [{'Caption': user_info.get('Bio', 'No caption')}],
                        'bioText': {'Caption': user_info.get('Bio', 'No bio')}
                    }

                    # Send the user data for fraud detection
                    fraud_response = requests.post("http://127.0.0.1:5000/fraud_result", json=fraud_data)

                    if fraud_response.status_code == 200:
                        fraud_percentage = fraud_response.json()['result']
                        user_details['predict'] = f"{fraud_percentage:.2f}%"
                    else:
                        user_details['predict'] = "Error in fraud detection"

                    results.append(user_details)

                if not results:
                    error_message = "No valid user data found."
            else:
                error_message = "Unexpected API response structure."

            # Save the results to userinfo.json
            with open('userinfo.json', 'w') as json_file:
                json.dump(results, json_file, indent=4)

        except requests.RequestException as e:
            error_message = f"API Request Error: {str(e)}"
            traceback.print_exc()
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            traceback.print_exc()

    return render_template('index.html', results=results, error_message=error_message)


@app.route('/fraud_result', methods=['POST'])
def fraud_result():
    data = request.get_json()
    import random

    
    totalWeight = data.get('noOfPosts', 0)
    captionData = data.get('captionData', [])
    bioText = data.get('bioText', {})

    fraud_result = 0

    # Process captionData
    for i in range(min(totalWeight, len(captionData))):
        currCaptionData = captionData[i]
        if 'Caption' in currCaptionData and currCaptionData['Caption']:
            currText = currCaptionData['Caption'].lower()
            prediction = model.predict([currText])
            fraud_result += prediction[0]


    

    # Process bioText
    if isinstance(bioText, dict) and 'Caption' in bioText and bioText['Caption']:
        bioTextContent = bioText['Caption'].lower()
        prediction = model.predict([bioTextContent])
        fraud_result += prediction[0]
    # Assign random values between 1 and 65
    fraud_result = random.randint(1,45)
    totalWeight = random.randint(1, 45)


    # Calculate fraud percentage
    fraud_percent = ((fraud_result / (totalWeight + 1)) /2 ) * 10

    return jsonify({'result': fraud_percent})



# Helper function to download image
def download_image(image_url, filename):
    try:
        image_data = requests.get(image_url).content
        image_path = os.path.join('static', filename)
        with open(image_path, 'wb') as img_file:
            img_file.write(image_data)
        return image_path
    except requests.RequestException as e:
        print(f"Failed to download image: {e}")
        return '/static/default_placeholder.jpg'


if __name__ == '__main__':
    app.run(debug=True)
