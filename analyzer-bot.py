#!/usr/bin/python
# Copyright (c) 2013 Dennis Waalewijn

import decimal
import time
import datetime
import sys
import pylab
import numpy as np

import btceapi 

class TickAnalyzer(object):
    '''Handle tickers, lastvalues and volatility'''
    
    ''' Define some variables that will be used, uses 
            input interval and listlength to configure 'window' of the analyzer '''
    def __init__(self, interval, listlength):
        self.interval = interval
        self.listlength = listlength
        self.lastValuesltcbtc = [0]*self.listlength #fill list of last values with zeroes
        self.changePercentage = [] #list not yet used
        self.marketTrendHistory = ["1"] # list to keep track of trend history, 1 = neutral, 2 = positive, 3 = negative
        self.iteration = 0 #times the analyzer retreived data
        self.trendisPositive = False
        self.trendisNegative = False
        self.trendisNeutral = True
        self.fee = 0.0
    
    def printTicker(self, pair, attrs):
        '''Modular print, prints all ticker values of one pair
            .. and saves them in a list of size 'listlength' '''
             
        print "*****************************************************"
        connection = btceapi.BTCEConnection()
        ticker = btceapi.getTicker(pair, connection)
        #currently only checking 1 pair
        print pair
            #for a in attrs: currently disabled because only checking 1 pair atm
        value = ticker.last
        print "\t%s %s" % (attrs, value)
        
        #fill list with found last value of pair
        self.lastValuesltcbtc.append(value)
        
        #iteration count to show how many checks have been done(will be used later)
        self.iteration = self.iteration+1

        connection.close()
    

    def listLastValues(self):
        ''' Use list of last values for calculations,
                print average of the list, the max and the min value of the list '''
        
        #calc window
        time = self.interval * self.listlength
        #print window
        print "Last", self.listlength, "lastvalues data, spread:", time, "seconds.", "Iteration:", self.iteration
        #calc values
        avg = float(sum(self.lastValuesltcbtc))/float(len(self.lastValuesltcbtc))
        maxlast = max(self.lastValuesltcbtc)
        minlast = min(self.lastValuesltcbtc)
        #print for convenience
        print "AVG:", avg
        print "max:", maxlast
        print "min:", minlast
            
    def checkVolatility(self):
        ''' Keeps track of volatility '''
        lastitem = self.lastValuesltcbtc[-1]
        secondlastitem = self.lastValuesltcbtc[-2]
        firstitem = self.lastValuesltcbtc[0]
        change = 1/100 #interval change
        cumchange = 1/100 #window change
        
        if secondlastitem>0:
            change = 100*((lastitem - secondlastitem)/secondlastitem)
        
        if firstitem>0:
            cumchange = 100*((lastitem - firstitem)/firstitem)

        self.changePercentage.append(change)
        curr = round(change, 6)
        wind = round(cumchange, 6)
        
        print "Current interval Volatility:", curr, "%", "Total Window Volatility:", wind, "%"
        
        return curr, wind
            
    def checkMarketDepth(self, pair):
        ''' Keeps track of current market depth '''
        connection = btceapi.BTCEConnection()
        asks, bids = btceapi.getDepth(pair, connection)
    
        ask_prices, ask_volumes = zip(*asks)
        bid_prices, bid_volumes = zip(*bids)
    
        a = np.array(bid_prices)
        b = np.array(bid_volumes)
        
        c = a*b #calc values and put them in list
        
        d = np.array(ask_prices)
        e = np.array(ask_volumes)
        
        f = d*e #calc valyes and put them in list
        
        suma = sum(ask_volumes)
        sumb = sum(bid_volumes)
        askspread = abs(max(bid_prices)-min(ask_prices)) #gap between buy and sell price
    
        print "Total askvolume:", suma, "with value:", f.sum() #print sum of lists
        print "Total bidvolume:", sumb, "with value:", c.sum()
        print "Lowest askprice:", min(ask_prices)
        print "Highest bidprice:", max(bid_prices)
        print "Ask-spread:", askspread
    
        connection.close()
    
    def marketTrend(self, threshold):
        ''' Returns the market trend from volatility in the window '''
        if self.iteration < self.listlength:
            print "List does not contain enough data, wait", (self.listlength-self.iteration)*self.interval, "seconds."
        else:
            
            curr, wind = self.checkVolatility()
            
            if curr >= -threshold and curr <= threshold and wind >= -threshold and wind <= threshold:
                self.trendisNeutral = True #1
                self.trendisPositive = False
                self.trendisNegative = False
                
                #match last market trend to current
                
                #neutral to neutral
                if self.marketTrendHistory[-1] == "1" and self.iteration >= 1:
                    print "Market Trend is still stable, wait for market signals"
                #postive to neutral
                elif self.marketTrendHistory[-1] == "2":
                    print "Market Trend is stagnating, time to sell"
                #negative to neutral
                elif self.marketTrendHistory[-1] == "3":
                    print "Market Trend is recovering, time to buy"
        
                self.marketTrendHistory.append("1")
        
            elif curr <= 0 and wind <= -threshold:
                self.trendisNegative = True #3
                self.trendisPositive = False
                self.TrendisNeutral = False
                
                #neutral to negative
                if self.marketTrendHistory[-1] == "1":
                    print "Market Trend is downwards, wait for market to recover"
                #postive to negative
                elif self.marketTrendHistory[-1] == "2":
                    print "Market Trend is steep downwards, time to sell/hold"
                #negative to negative
                elif self.marketTrendHistory[-1] == "3":
                    print "Market Trend is still downwards, wait for market to recover"
        
                self.marketTrendHistory.append("3")
                    
            elif curr >= 0 and wind >= threshold:
                self.trendisNegative = False
                self.trendisPositive = True #2
                self.TrendisNeutral = False
                
                #neutral to positive
                if self.marketTrendHistory[-1] == "1":
                    print "Market Trend is upwards, wait for market to stagnate"
                #postive to positive
                elif self.marketTrendHistory[-1] == "2":
                    print "Market Trend is still upwards, wait for market to stagnate"
                #negative to positive
                elif self.marketTrendHistory[-1] == "3":
                    print "Market Trend is steep upwards, time to buy/hold"
                
                self.marketTrendHistory.append("2")
        
        self.updateList() #update lists of calculated values
                
                
    def getFees(self, pair):
        ''' Retreive current fees on transactions of given pair '''
        connection = btceapi.BTCEConnection()
        self.fee = btceapi.getTradeFee(pair, connection)
        connection.close()
        return self.fee

    def showLastTrades(self, pair):
        ''' Show last ask and bid trades of current window '''
        connection = btceapi.BTCEConnection()
        window = self.interval*self.listlength
        timediff = datetime.timedelta(seconds=window)
        sellvalue = 0
        buyvalue = 0
        sellamount = 0
        buyamount = 0
        countask = 0
        countbid = 0
            
        history = btceapi.getTradeHistory(pair, connection)
        # print "History length:", len(history) unnecessary
        
        for h in history:
            
            if h.trade_type == u'ask' and h.date >= (datetime.datetime.now() - timediff):
        #give total amount of ask trades of last window
                countask += 1
                sellamount += h.amount
                sellvalue += (h.amount*h.price)
            elif h.trade_type == u'bid' and h.date >= (datetime.datetime.now() - timediff):
        #give total amount of bid trades of last window
                countbid += 1
                buyamount += h.amount
                buyvalue += (h.amount*h.price)

        print "Number of sell trades:", countask, "Total amount: %s BTC" % sellamount, "With value: %s EUR" % sellvalue
        print "Number of buy trades: ", countbid, "Total amount: %s BTC" % buyamount, "With value: %s EUR" % buyvalue
        
        connection.close()
                
    def updateList(self):
        ''' When list size is bigger than given length argument,
                pop first item '''
        if len(self.changePercentage) == self.listlength+1:
            self.changePercentage.pop(0)
        
        if len(self.lastValuesltcbtc) == self.listlength+1:
            self.lastValuesltcbtc.pop(0)
        
        if len(self.marketTrendHistory) > 2: #only keeping track of last 2 values
            self.marketTrendHistory.pop(0)

    # not used
    def graphDepth(self, pair):
        ''' Build a graph to show depth of given pair '''
        asks, bids = btceapi.getDepth(pair)

        ask_prices, ask_volumes = zip(*asks)
        bid_prices, bid_volumes = zip(*bids)

        pylab.plot(ask_prices, np.cumsum(ask_volumes), 'r-')
        pylab.plot(bid_prices, np.cumsum(bid_volumes), 'g-')
        pylab.grid()
        pylab.title("%s depth" % pair)
        pylab.show()
        pylab.close()
    #not used
    def graphHistory(self, pair):
        ''' Build graph of trade history of pair '''
        history = btceapi.getTradeHistory(pair)

        print "History length:", len(history)

        pylab.plot([t.date for t in history if t.trade_type == u'ask'],
           [t.price for t in history if t.trade_type == u'ask'], 'ro')

        pylab.plot([t.date for t in history if t.trade_type == u'bid'],
           [t.price for t in history if t.trade_type == u'bid'], 'go')

        pylab.grid()
        pylab.show()
        pylab.close()

    def showAccountInfo(self, keyfile):
        ''' Show account info such as
            balance and total value of wallet '''
        handler = btceapi.KeyHandler(keyfile, resaveOnDeletion=True)
        
        for key in handler.getKeys():
            # print "Printing info for key %s" % key
            
            conn = btceapi.BTCEConnection()
            t = btceapi.TradeAPI(key, handler=handler)

    
        try:
            r = t.getInfo(connection = conn)
            print "\t*************"
        
            for currency in btceapi.all_currencies:
                balance = getattr(r, "balance_" + currency)
                if balance != 0:
                    print "\t%s balance: %s" % (currency.upper(), balance)
        
        # print "\tInformation rights: %r" % r.info_rights
        # print "\tTrading rights: %r" % r.trade_rights
        # print "\tWithrawal rights: %r" % r.withdraw_rights
            print "\tServer time: %r" % str(r.server_time)
                
                #compute estimated account value too
            exchange_rates = {}
            for pair in btceapi.all_pairs:
                asks, bids = btceapi.getDepth(pair)
                exchange_rates[pair] = bids[0][0]
                    
            btc_total = 0
            for currency in btceapi.all_currencies:
                balance = getattr(r, "balance_" + currency)
                if currency == "btc":
                    # print "\t%s balance: %s" % (currency.upper(), balance)
                    btc_total += balance
                else:
                    pair = "%s_btc" % currency
                if pair in btceapi.all_pairs:
                    btc_equiv = balance * exchange_rates[pair]
                else:
                    pair = "btc_%s" % currency
                    btc_equiv = balance / exchange_rates[pair]
                            
                    bal_str = btceapi.formatCurrency(balance, pair)
                    btc_str = btceapi.formatCurrency(btc_equiv, "btc_usd")
                            #print "\t%s balance: %s (~%s BTC)" % (currency.upper(), bal_str, btc_str)
                    btc_total += btc_equiv
                    
                    #print "\tCurrent value of open orders:"
            orders = t.activeOrders(connection = conn)
            if orders:
                for o in orders:
                    btc_equiv = o.amount * exchange_rates[o.pair]
                    btc_str = btceapi.formatCurrency(btc_equiv, pair)
                    print "\t\t%s %s %s @ %s (~%s BTC)" % (o.type, o.amount, o.pair, o.rate, btc_str)
                    btc_total += btc_equiv
            else:
                print "\t\tThere are no open orders."
                    
            btc_str = btceapi.formatCurrency(btc_total, "btc_eur")
            print "\tTotal estimated value: %s BTC" % btc_str
                    # for fiat in ("eur"):
            fiat_pair = "btc_%s" % "eur"
            fiat_total = btc_total * exchange_rates[fiat_pair]
            fiat_str = btceapi.formatCurrencyDigits(fiat_total, 2)
            print "\t                       %s EUR" % fiat_str
            print "\t*************"

    #print "\tItems in transaction history: %r" % r.transaction_count
        except:
            print " An error occurred: kakzooi"
            raise

def run(pair, listlength, threshold, interval, keyfile):
    print "Showing TickerAnalyzer results, press Ctrl-C to stop"
    analyzer = TickAnalyzer(interval, listlength)
    while True:
        time.sleep(interval)
        analyzer.printTicker(pair, 'last')
        analyzer.listLastValues()
        analyzer.checkMarketDepth(pair)
        analyzer.marketTrend(threshold)
        analyzer.showLastTrades(pair)
        #analyzer.showAccountInfo(keyfile)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Simple market analyzer example.')
    parser.add_argument('interval', type=int,
                        help='Time between analyzes in seconds')
    parser.add_argument('listlength', type=int,
                            help='Time between analyzes in seconds')
    parser.add_argument('threshold', type=float,
                            help='Time between analyzes in seconds')
    parser.add_argument('pair',
                        help='Time between analyzes in seconds')
    parser.add_argument('keyfile',
                            help='Filename and extension of API keys')
    args = parser.parse_args()
    run(args.pair, args.listlength, args.threshold, args.interval, args.keyfile)

# Python is awesome
