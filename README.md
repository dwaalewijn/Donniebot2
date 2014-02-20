Donniebot2
==========
Only does some BTC-E information scraping, simple calculations and
print in console. Be sure to adjust keysfile.txt accordingly.

Args:
Interval: Seconds between retrieving information of BTC-E
Listlength: Number of values stored in list (Time window =
interval*listlength
threshold: threshold of when a trend is a trend (standard 0.2)
trade pair: trade pair to keep track of
keysfile

Usage example: python analyzer-bot.py 30 30 0.4 btc_eur keysfile.txt
