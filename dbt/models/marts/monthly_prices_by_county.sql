select
    sale_month,
    county,
    property_type,
    count(*) as sales,
    median(price) as median_price
from {{ ref('stg_price_paid') }}
group by sale_month, county, property_type
