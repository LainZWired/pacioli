http://api.bitcoincharts.com/v1/csv/

Download bitstampUSD.csv.gz 

querycsv.py -i bitstampUSD.csv -o bitstampUSD-summarized.csv "SELECT timestamp, sum(price*quantity) / sum(quantity) AS VWAP FROM bitstampUSD GROUP BY timestamp;"


Save the summarized file to the price_data directory, move the raw file elsewhere.
