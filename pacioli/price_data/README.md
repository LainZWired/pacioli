http://api.bitcoincharts.com/v1/csv/

Download bitstampUSD.csv.gz 

Command line:

<code> querycsv.py -i bitstampUSD.csv -o bitstampUSD-summarized.csv "SELECT datetime(timestamp, 'unixepoch') AS timestamp,  'bitstamp' AS source, 'USD' as currency, cast(((sum(price*(quantity+1)) / sum(quantity+1)*100)) as int) AS rate FROM bitstampUSD GROUP BY timestamp;" </code>

<code>psql pacioli</code>

<code> COPY prices FROM '/Users/Rochard/sni-src/pacioli/test_files/_data/bitstampUSD-summarized.csv' DELIMITER ',' HEADER CSV;</code>
