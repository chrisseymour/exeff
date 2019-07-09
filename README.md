# exeff

named after the Ex/Eff (ex dividend date) column of the Nasdaq.com dividend history

Use requests and Beautiful Soup to get the dividend [price history](https://www.nasdaq.com/symbol/kmb/historical) and [dividend history](https://www.nasdaq.com/symbol/kmb/dividend-history).

 - Uses a POST request to get desired the price history range.

Calculate the dividend increase history, and use the history to predict the future Yield on Cost 5, 10, 20 years out.

Calculate the Historical Yield on Cost, which shows the yield investors were expecting at that time in the past.
 - four times the upcoming dividend ammount, divided by the stock price at that time.
 - measure, similar to price/earnings, to determine whether a stock is 'on sale' or 'overpriced'
 
 Use the dividend increase distribution, to get a range of possible future yield on costs, instead of a single, average value.

