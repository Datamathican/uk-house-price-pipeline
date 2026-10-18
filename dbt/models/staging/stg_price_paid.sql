-- Clean and type the raw Price Paid rows.
select
    transaction_id,
    price,
    cast(date_of_transfer as date) as sale_date,
    date_trunc('month', cast(date_of_transfer as date)) as sale_month,
    upper(trim(postcode)) as postcode,
    case property_type
        when 'D' then 'Detached'
        when 'S' then 'Semi-detached'
        when 'T' then 'Terraced'
        when 'F' then 'Flat/Maisonette'
        else 'Other'
    end as property_type,
    new_build = 'Y' as is_new_build,
    case tenure when 'F' then 'Freehold' when 'L' then 'Leasehold' end as tenure,
    upper(town_city) as town_city,
    upper(district) as district,
    upper(county) as county
from {{ source('raw', 'price_paid') }}
-- Category B (repossessions, buy-to-let, etc.) is excluded; A = standard sales
where ppd_category = 'A'
  and record_status != 'D'  -- D = deleted records
