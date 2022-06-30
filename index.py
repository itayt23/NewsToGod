import asyncio
from api_context import Context
import requests



async def main():

	ctx = Context()
	#ctx.initialize(application)
	await ctx.initialize()

	url = "https://api.tradestation.com/v3/marketdata/barcharts/MSFT"
	headers = {"Authorization": f'Bearer {ctx.TOKENS.access_token}'}
	response = requests.request("GET", url, headers=headers)
	print(response.text)



if __name__ == '__main__':
	asyncio.run(main())
	



