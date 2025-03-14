# chatGPT-bot
A bot that analyses screen shots of dextools and give recommandation on possible trade

![Screenshot](Screenshot%202025-03-14%20at%2006.25.30.png)

# 📊 AI-Powered Meme Coin Trading Bot  

## 🚀 Overview  
This tool automates technical analysis for meme coins using ChatGPT. Users simply take a screenshot of a token’s chart, and the system analyzes whether it's a good entry point. If conditions are met, the trade is executed automatically.  

## 🛠 How It Works  
1. The user **takes a screenshot** of the meme coin chart they wish to analyze.  
2. The screenshot is **sent to ChatGPT** for technical analysis using a predefined prompt.  
3. ChatGPT **extracts key trading data** and determines whether it's a good entry point.  
4. If the probability of success is **above 60% (configurable)**, the trade is executed.  

## 🔍 ChatGPT Analysis Prompt  
The following prompt is used to analyze the chart and generate trading decisions:  

This chart has a 15min resolution of a meme coin. I want you to analyse this chart and tell me if it is a good entry price now and give me a short-term target price.

To get the current price, look at the box in the top-right corner in big characters, preceded by the $ sign.
To get the name of the token, look at the top-left corner, on the right side of the logo image, and use the text on top of the block that shows the token name above and the pair name below.

Ensure the following conditions:

stop_loss < entry_price * 0.9
target_price > entry_price
If the chances of success are above 60%, return the following JSON format:


{ 
  "entry_price": "", 
  "target_price": "", 
  "stop_loss": "", 
  "token_name": "", 
  "chances_of_success": "" 
}
If the chances of success are below 60%, return:

"No go for trade"

