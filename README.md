# chatGPT-bot
A bot that analyses screen shots of dextools and give recommandation on possible trade

![Screenshot](Screenshot%202025-03-14%20at%2006.25.30.png)

The user simply takes screenshots of the tokens he wishes to analyse, then the screenchot is sent to chatGPT for Technical Analysis, with the following prompt:

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

And then trade is executed if chances_of_success is above 60% (configurable), the trade is executed.
