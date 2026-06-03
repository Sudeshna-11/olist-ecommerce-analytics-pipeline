{#
    Convert a BRL amount to a quote currency given an already-joined daily
    FX rate. Centralises the multiply + rounding + numeric type so every
    fact converts money the same way. A null fx_rate (a date before the
    rate series begins) yields null, which is the honest result.

    Usage:
        {{ convert_brl('item_price_brl', 'fx_brl_usd') }} as item_price_usd
#}

{% macro convert_brl(brl_amount, fx_rate) %}
    cast({{ brl_amount }} * {{ fx_rate }} as numeric(14, 2))
{% endmacro %}
