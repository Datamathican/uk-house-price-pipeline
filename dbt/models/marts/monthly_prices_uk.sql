select
    sale_month,
    count(*) as sales,
    median(price) as median_price,
    avg(price) as mean_price
from {{ ref('stg_price_paid') }}
group by sale_month
