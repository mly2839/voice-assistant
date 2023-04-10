import asyncio
import re
from EdgeGPT import Chatbot, ConversationStyle

async def main():
    # starting up the bing ai bot using the cookies for the newest edge (required to use Bing AI)
    bingBot = Chatbot(cookiePath='cookies.json')

    # Asking a question and awaiting the response
    response = await bingBot.ask(prompt=input("Ask Bing AI a question... "), conversation_style = ConversationStyle.creative)
    
    # Filtering the message to just display a response and not the whole json
    for message in response["item"]["messages"]:
        if message["author"] == "bot":
            botResponse = message["text"]

    # Filtering out links using a regex
    botResponse = re.sub('\[\^\d+\^\]', '', botResponse)

    # Printing the Response
    print("Bot Response: ", botResponse)

    #closing the bot
    await bingBot.close()


if __name__ == "__main__":
    asyncio.run(main())