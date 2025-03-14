import os
import shutil
import time
import openai
import json
from PIL import Image
import base64
import requests
from playwright.sync_api import sync_playwright

from solana.rpc.api import Client
import pandas as pd

MIN_STOP_LOSS = 0.1
acceptable_risk_reward = 1.5
# Jupiter Aggregator API endpoint
JUPITER_API_URL = "https://quote-api.jup.ag/v6/quote"


def read_token_file(file_path):
    """
    Reads a CSV file containing token names and addresses, and stores them in a dictionary (map).
    
    :param file_path: Path to the CSV file (e.g., ~/Downloads/meme_trade_tokens.csv)
    :return: A dictionary with token names as keys and token addresses as values
    """
    # Read the CSV file into a pandas DataFrame, using semicolon as the delimiter
    df = pd.read_csv(file_path, sep=';')
    
    # Strip any potential leading/trailing spaces from column names
    df.columns = df.columns.str.strip()

    # Convert the columns to a dictionary (assuming first row is headers)
    token_map = dict(zip(df['token_name'], df['token_address']))
    
    return token_map



def get_token_address(token_map, token_name):
    """
    Retrieve the token address based on the token name.
    
    :param token_map: Dictionary containing token name and address pairs
    :param token_name: The name of the token to search for
    :return: Token address if found, otherwise None
    """
    return token_map.get(token_name.upper(), "Token not found")


def remove_files_from_desktop():
    # Get the path to the Desktop directory
    desktop_path = os.path.expanduser("~/Desktop")
    
    # Check if the directory exists
    if not os.path.exists(desktop_path):
        print("Desktop directory does not exist.")
        return
    
    # Loop through all files in the Desktop directory
    for filename in os.listdir(desktop_path):
        file_path = os.path.join(desktop_path, filename)
        
        # Check if the path is a file, and if so, remove it
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Removed file: {file_path}")
        # Optionally, you can also remove directories
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
            print(f"Removed directory: {file_path}")




def get_token_to_usdc_quote(token_address, amount, slippage=1):
    """
    Fetches the best swap quote from the Jupiter Aggregator for SOL to USDC.

    :param amount: The amount of SOL in lamports (1 SOL = 1_000_000_000 lamports)
    :param slippage: Slippage tolerance percentage
    """
    # Mint addresses
    TOKEN_MINT = token_address  # wSOL
    #SOL_MINT = "So11111111111111111111111111111111111111112"  # wSOL

    USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # Correct USDC mint address on Solana

    params = {
        "inputMint": TOKEN_MINT,
        "outputMint": USDC_MINT,
        "amount": str(amount),  # Ensure amount is passed as a string
        "slippageBps": str(int(slippage * 100)),  # Slippage in basis points (1% = 100 bps)
    }

    response = requests.get(JUPITER_API_URL, params=params, timeout=10)

    if response.status_code == 200:
        data = response.json()
        #print(data)
        if "inAmount" in data and len(data["inAmount"]) > 0:
            price_in_usdc = float(data['outAmount']) /float(data['inAmount'])
            print(f"price_in_usdc: {price_in_usdc}")
        else:
            print("No routes found for this pair.")
    else:
        # Print detailed error message if response status code is not 200
        print(f"Failed to fetch data from Jupiter API. Status code: {response.status_code}")
        try:
            error_message = response.json().get("error", "No error message provided")
            print(f"Error message: {error_message}")
        except Exception as e:
            print(f"Error details could not be retrieved: {e}")




frequency = 2500  # Set Frequency To 2500 Hertz
duration = 1000  # Set Duration To 1000 ms == 1 second

# Set your OpenAI API key
openai.api_key = "YOUR_OPENAI_KEY"

# Set the path to the Desktop directory
DESKTOP_DIR = os.path.expanduser("~/Desktop")
CHECK_INTERVAL = 5  # Check every 1 minute

# Store the file names of already analyzed images
analyzed_images = set()


def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


# Function to send the image and text to ChatGPT API
def send_to_chatgpt(image_path):
    with open(image_path, "rb") as image_file:

        base64_image = encode_image(image_path)


        # Create a prompt to send to ChatGPT
        prompt = """
        This chart has a 15min resolution of a meme coin. I want you to analyse this chart and tell me if it is a good entry price now and give me a short term target price. To get the current price, look at the box in top right corner in big characters and preceeded by the $ sign. To get the name of the token, look at the top left corner, on the right side of the logo image, and use the text on top of the block that shows the token name above and the pair name below.         
        I want you to make sure that the stop_loss is lower than the entry_price*0.9 in your response. 
        I want you to make sure that target_price > entry_price in your response.
        If the chances of success are above 60% per your estimation, I want you to answer only the following elements: entry price, target price, stop loss, token name, chances of success of the trade if made.
        All the values in your response must be numerical values only with no additional text.
        I want these 5 elements in a json format exactly like that: {
            "entry_price" : "",
            "target_price" : "",
            "stop_loss" : "",
            "token_name" : "",
            "chances_of_success" : ""
        } 

        If the chances of success are below 60% per your estimation, I want you to return "No go for trade".
        """

        # Send the image and prompt to OpenAI's API (text-davinci-004 if available, otherwise use gpt-4 or gpt-3.5-turbo)
        try:
           
            headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai.api_key}"
            }

            payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": prompt
                    },
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                    }
                ]
                }
            ],
            "max_tokens": 300
            }

            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

            response_dict = response.json()    # <--- convert to dictionary
            response_message = response_dict["choices"][0]["message"]["content"].strip()  # <--- lookup the dict

            return response_message
        except Exception as e:
            print(f"Error sending request to OpenAI API: {e}")
            return None

# Function to check for new images
def check_for_new_images(token_map):
    for filename in os.listdir(DESKTOP_DIR):
        if filename.endswith(('.png', '.jpg', '.jpeg')) and filename not in analyzed_images:
            image_path = os.path.join(DESKTOP_DIR, filename)
            print(f"Analyzing new image: {filename}")

            # Send the image and prompt to ChatGPT API
            result = send_to_chatgpt(image_path)
            #print(type(result))
            cleaned_response = result.replace("```json", "").replace("```", "").strip()

            # Display the result in the console
            if result:
                try:
                    print("+++++++++++ NEW CHART ++++++++++++")
                    result_json = json.loads(cleaned_response)
                    chances_of_success = result_json.get("chances_of_success", "N/A")
                    if (not isinstance(chances_of_success, int) ):
                        chances_of_success = chances_of_success.replace("%", "").strip()

                    token_name = result_json.get("token_name", "N/A")
                    entry_price = float(result_json.get("entry_price", "N/A"))
                    target_price = float(result_json.get("target_price", "N/A"))
                    stop_loss = float(result_json.get("stop_loss", "N/A"))


                    if (stop_loss > (entry_price * (1-MIN_STOP_LOSS))):
                        print('problem with the stop loss:', stop_loss)
                        stop_loss = entry_price * (1-MIN_STOP_LOSS)
                        print('new stop loss:', stop_loss)

                    # Retrieve a token address by name
                    token_address = get_token_address(token_map, token_name)

                    print(f"Token Address for {token_name}: {token_address}")

                    print(f"Token: {token_name}")
                    print(f"Chances of Success: {chances_of_success}")
                    print(f"entry_price: {entry_price}")
                    print(f"target_price: {target_price}")
                    print(f"stop_loss: {stop_loss}")
                    risk_reward_ratio = round((target_price - entry_price) / (entry_price - stop_loss),2)
                    is_good_trade = risk_reward_ratio >= acceptable_risk_reward
                    print(f"Risk/Reward Ratio: {risk_reward_ratio:.2f}")
                    print(f"Is this a good trade? {'Yes' if is_good_trade else 'No'}")
                    if (is_good_trade) :
                        os.system('say "Going to execute the trade!" ')
                        break_even_win_rate_calc = 1 / (1+risk_reward_ratio)
                        print(f"break_even_win_rate_calc: {round(round(break_even_win_rate_calc,2)*100)}%")

                except json.JSONDecodeError:
                    print("Failed to parse the result as JSON.")
                    print("Raw result:", result)
            if result:
                print("Chart analyze success!")
            else:
                print("Failed to analyze the image.")

            # Mark the image as analyzed
            analyzed_images.add(filename)
            get_token_to_usdc_quote(token_address, AMOUNT_IN_LAMPORTS)
        


if __name__ == "__main__":
    print("Starting the trading bot...")
    remove_files_from_desktop()
    # Example usage
    file_path = '~/Downloads/meme_trade_tokens.csv' 

    # Read the token file and store the pairs in a map
    token_map = read_token_file(file_path)

    while True:

        AMOUNT_IN_SOL = 1  # 1 SOL
        AMOUNT_IN_LAMPORTS = AMOUNT_IN_SOL * 1_000_000_000
        check_for_new_images(token_map)

        
        time.sleep(CHECK_INTERVAL)
