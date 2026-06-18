# Power BI build walkthrough — Olist 5-page report (beginner edition)

This guide builds the file `dashboards/olist_analytics.pbix` from nothing. It assumes you have **never used Power BI before**. Every click is spelled out, and after each action it tells you **what you should see on screen** so you know it worked.

Work through it top to bottom. Don't skip Phase B — it's the step that stops the numbers from being wrong.

- Where each chart goes and why: [dashboards.md](dashboards.md)
- Connection details + all the formulas: [powerbi-connection.md](powerbi-connection.md)

---

## A few words you'll see a lot (plain-English glossary)

| Word | What it actually means |
|---|---|
| **Visual** | Any chart, map, table, or number box on the page. |
| **Card** | A box that shows one big number (e.g. total revenue). |
| **Measure** | A saved calculation (like a formula in Excel). You make these once and reuse them. |
| **DAX** | The little formula language used to write a measure. You'll copy-paste these — you don't have to write them. |
| **Aggregate / mart / table** | A pre-built table of summarized data living in Snowflake. There are five; each one feeds one page. |
| **Field / column** | One piece of data in a table, e.g. `gmv_brl` (revenue) or `state`. |
| **Well** | A drop-zone in Power BI where you drag a field to put it on a chart (e.g. the "X-axis" box). |
| **Pane** | A panel on the side of the screen. |

---

## 0. Get your bearings — what's on the screen

Open Power BI Desktop. Close the welcome/splash window if one pops up. Now look at the screen. There are **five areas** you'll use constantly:

1. **The ribbon** — the strip of buttons across the very top, with tabs named **Home, Insert, Modeling, View**. (Like the buttons at the top of Word or Excel.)
2. **The canvas** — the big empty white area in the middle. This is your report page. Your charts go here.
3. **Page tabs** — along the **bottom**, like the sheet tabs in Excel. Right now there's probably one called "Page 1".
4. **Three small icons on the far LEFT edge**, stacked vertically. These switch what you're looking at:
   - 📊 top icon = **Report view** — where you build charts. *You'll be here almost the whole time.*
   - ▦ middle icon = **Table view** — shows the raw data as a grid.
   - 🔗 bottom icon = **Model view** — shows how tables connect.
5. **Two panes on the far RIGHT:**
   - **Visualizations** pane (middle-right) — a grid of small chart-type icons. This is your "chart menu".
   - **Data** pane (far right) — a list of your tables. Click the little arrow ▸ next to a table name to open it and see its columns.

> **The one move you'll repeat over and over:**
> 1. Click a chart icon in the **Visualizations** pane → an empty chart appears on the canvas.
> 2. Drag field names from the **Data** pane (far right) into the boxes ("wells") that appear under the chart icons.
> That's it. Every page is just this move, repeated.

---

## ⚠️ The single most important thing to understand before you build

When you click on a chart to select it, the **Visualizations** pane shows some boxes called **wells** (like "X-axis", "Y-axis"). But there are **two little sub-tabs** controlling what you see, sitting just under the row of chart icons:

- An icon that looks like a **small bar chart with fields** → this is the **"Build visual"** tab. ← **You want this one.** It shows the wells where you drag fields.
- An icon that looks like a **paint roller** 🛞 → this is the **"Format visual"** tab. It shows colors and fonts, **no wells**.

**If you ever don't see "X-axis / Y-axis" or other wells:**
- Make sure you have **clicked on the chart first** (so it's selected — you'll see a border and corner dots).
- Make sure the **bar-chart sub-tab (Build)** is active, not the paint roller.

Also: the well names change depending on the chart and your Power BI version. For a line or column chart you'll see **either** "X-axis / Y-axis" **or** the older "Axis / Values". They mean the same:
- **X-axis** = **Axis** = the bottom (categories / dates)
- **Y-axis** = **Values** = the height (the numbers)

Keep this in mind for every step below.

---

## Phase A — Connect to Snowflake (get the data in)

**Goal:** pull the five data tables out of Snowflake into Power BI.

You need one piece of info first: your Snowflake **account name** — it's the bit of your Snowflake web address *before* `.snowflakecomputing.com` (for example `ab12345.eu-west-1`). It's saved in the project file `.secrets.env` as `SNOWFLAKE_ACCOUNT`. Open that file yourself and copy the value.

1. On the **Home** ribbon, click **Get Data** → in the menu, click **More…**
   *You'll see:* a window listing data sources.
2. In the search box, type `Snowflake`. Click **Snowflake** in the list → click **Connect** (bottom right).
3. A small window asks for two things:
   - **Server:** type `youraccount.snowflakecomputing.com` (replace `youraccount` with your real account name).
   - **Warehouse:** type `COMPUTE_WH`
4. Click the little arrow next to **Advanced options** to expand it. In the **Role** box, type `PBI_READER` (this is a safe read-only login). *If you haven't set that up yet, leave it blank for now — it'll still work.*
5. Below that, find **Data Connectivity mode**. Click the top circle, **Import**. (Not "DirectQuery".)
6. Click **OK**.
7. A login box appears. Click the **Snowflake** tab on the left, type your Snowflake **username and password**, click **Connect**.
   *You'll see:* a window titled **Navigator** with a tree of names on the left.
8. In that tree, click the arrows to open `OLIST`, then `ANALYTICS_marts`. You'll see table names. **Tick the checkbox** next to all five:
   - `MART_DAILY_REVENUE`
   - `MART_CATEGORY_REVENUE`
   - `MART_STATE_PERFORMANCE`
   - `MART_SELLER_PERFORMANCE`
   - `MART_CUSTOMER_COHORTS`
9. Click the **Load** button (bottom right).
   *You'll see:* after a moment, the five table names appear in the **Data** pane on the far right. ✅ Data is in.

> **Stuck?** If you don't see `ANALYTICS_marts` in the tree, your login probably can't see it — note the exact message and ask for help before continuing.

---

## Phase B — Fix the data types (do NOT skip — this prevents wrong numbers)

**Why:** by default, Power BI tries to **add up** every number column. That's fine for revenue, but disastrous for things that are already percentages or averages — it would, for example, "add up" on-time percentages into a meaningless 4,000%. We tell Power BI: *don't add these up.*

1. Click the **Table view** icon (the ▦ middle icon on the far-left edge).
   *You'll see:* a grid of data, and your table list on the right.
2. Click a table name on the right (start with `MART_STATE_PERFORMANCE`).
3. Click once on a **column heading** in the grid. A new ribbon tab called **Column tools** lights up at the top.
4. On that **Column tools** ribbon there are two dropdowns you'll use:
   - **Data type** — what kind of value it is.
   - **Summarization** — set this to **Don't summarize** for the columns listed below.

Now go column by column and apply these rules. **You do this for all five tables**, but only for whichever of these columns each table actually has:

| If the column name… | Set Data type to | Set Summarization to |
|---|---|---|
| ends in `_brl`, `_usd`, `_eur`, or starts with `gmv_` / `revenue_` | **Fixed decimal number** (then format as Currency) | leave as is |
| is `date_day` or `cohort_month` | **Date** | — |
| starts with `n_` (a count, e.g. `n_orders`, `n_customers`) | Whole number | **Don't summarize** |
| is `on_time_pct`, `avg_review_score`, `avg_delivery_days`, `repeat_rate_pct`, `avg_orders_per_customer`, or `avg_clv_brl` | Decimal number | **Don't summarize** |
| is `date_key` or `purchase_date_key` | Whole number | **Don't summarize** |

> Don't worry about being perfect on the currency formatting — the important part is setting **"Don't summarize"** on every count (`n_...`) and every average/percentage column. That's the bit that keeps the dashboard honest.

When done, go back to **Report view** (📊 top-left icon).

---

## Phase C — Create the measures (your reusable formulas)

**Why:** instead of dragging raw columns (which can be added up wrongly), we make safe, correct **measures** once and reuse them. You'll copy-paste them — no need to understand the formula text.

**Step 1 — make a home for them:**
1. **Home** ribbon → **Enter Data**.
   *You'll see:* a little empty table editor.
2. Don't type any data. Near the bottom, change the table name to `_Measures` (the underscore makes it sort to the top). Click **Load**.
   *You'll see:* a new `_Measures` table in the Data pane.

**Step 2 — add each measure (repeat for every formula):**
1. In the **Data** pane, **right-click** `_Measures` → click **New measure**.
   *You'll see:* a formula bar appear across the top (looks like a long text box with `Measure =` in it).
2. **Select all** the text in that bar and **paste one full line** from below (the whole thing, including the name and the `=`).
3. Press **Enter**.
   *You'll see:* a small **calculator icon** 🧮 next to a new name in `_Measures`. ✅ That measure is done.
4. If you see a **red error** instead, you probably pasted only half a line — clear it and paste a full line again.
5. Repeat for the next formula.

> **Tip:** only add the measures for the page you're about to build. Below they're grouped by page. Start with the **Page 1** group. Come back for the others when you reach those pages.
>
> **Order matters in two spots:** a couple of formulas use other measures inside them (e.g. `Avg Order Value` uses `GMV (BRL)` and `Orders`). Just paste them in the order shown and you'll be fine.

### Page 1 measures — paste these first
```dax
GMV (BRL)             = SUM(mart_daily_revenue[gmv_brl])
Merch Revenue (USD)   = SUM(mart_daily_revenue[items_usd])
Freight (BRL)         = SUM(mart_daily_revenue[freight_brl])
Orders                = SUM(mart_daily_revenue[n_orders])
Items                 = SUM(mart_daily_revenue[n_items])
Avg Order Value (BRL) = DIVIDE([GMV (BRL)], [Orders])
```

### Page 2 measures
```dax
State Orders      = SUM(mart_state_performance[n_orders])
State GMV (BRL)   = SUM(mart_state_performance[gmv_brl])
Delivered Orders  = SUM(mart_state_performance[n_delivered])
On-Time Orders    = SUM(mart_state_performance[n_on_time])
On-Time %         = DIVIDE([On-Time Orders], [Delivered Orders])
Avg Delivery Days =
    DIVIDE(
        SUMX(
            mart_state_performance,
            mart_state_performance[avg_delivery_days] * mart_state_performance[n_delivered]
        ),
        [Delivered Orders]
    )
```

### Page 3 measures
```dax
Category Revenue (BRL) = SUM(mart_category_revenue[revenue_brl])
Category Revenue (USD) = SUM(mart_category_revenue[revenue_usd])
Categories Tracked     = DISTINCTCOUNT(mart_category_revenue[category])
Revenue % of Total =
    DIVIDE(
        [Category Revenue (BRL)],
        CALCULATE([Category Revenue (BRL)], REMOVEFILTERS(mart_category_revenue))
    )
```

### Page 4 measures
```dax
Active Sellers       = DISTINCTCOUNT(mart_seller_performance[seller_key])
Seller Revenue (BRL) = SUM(mart_seller_performance[revenue_brl])
Total Reviews        = SUM(mart_seller_performance[n_reviews])
Avg Review Score =
    DIVIDE(
        SUMX(
            mart_seller_performance,
            mart_seller_performance[avg_review_score] * mart_seller_performance[n_reviews]
        ),
        [Total Reviews]
    )
```

### Page 5 measures
```dax
Total Customers       = SUM(mart_customer_cohorts[n_customers])
Repeat Customers      = SUM(mart_customer_cohorts[n_repeat_customers])
Total Customer Orders = SUM(mart_customer_cohorts[total_orders])
Lifetime GMV (BRL)    = SUM(mart_customer_cohorts[gmv_brl])
Repeat Rate %         = DIVIDE([Repeat Customers], [Total Customers])
Orders per Customer   = DIVIDE([Total Customer Orders], [Total Customers])
Avg CLV (BRL)         = DIVIDE([Lifetime GMV (BRL)], [Total Customers])
```

> The complete set with extra optional measures and the reasoning behind each is in [powerbi-connection.md](powerbi-connection.md#dax-measures).

**One more thing — leave the tables unconnected.** Click the 🔗 **Model view** icon (far-left). You'll see your five tables as boxes. They should have **no lines joining them**. If you see a line between any two, click the line and press **Delete**. (This is on purpose — each page uses its own table.)

---

## Page 1 — Executive Overview

This is the page you do most carefully, because every other page is the same steps with different fields.

**Rename the page:** double-click the tab at the bottom (e.g. "Page 1") → type `Executive Overview` → Enter.

### Part 1 — four number boxes (KPI cards) across the top

1. In the **Visualizations** pane, find the **Card** icon — it shows a single number like **`123`**. (Not "Multi-row card".) Click it once.
   *You'll see:* an empty box appear on the canvas.
2. Drag that box to the top-left. Drag a corner dot to make it small (about one-sixth of the width).
3. Make sure the box is selected (border showing) and the **Build** sub-tab (bar-chart icon, not paint roller) is active. You'll see a well called **Fields**.
4. In the **Data** pane, open `_Measures` (click the ▸ arrow). Drag **`GMV (BRL)`** into the **Fields** well.
   *You'll see:* the card now shows a big revenue number. ✅
5. **Quick way to make the next three:** click the card, press **Ctrl+C** then **Ctrl+V** to copy it. Move the copy next to the first. In the copy's **Fields** well, click the small **X** next to `GMV (BRL)` to remove it, then drag in the next measure.
6. Do that for **`Orders`**, then **`Items`**, then **`Avg Order Value (BRL)`**.
   *You'll see:* a row of four number boxes. ✅

### Part 2 — the big line chart (revenue over time)

1. **Click an empty part of the canvas first** (so the next chart isn't added inside a card).
2. In **Visualizations**, click the **Line chart** icon (a zig-zag line). An empty chart appears.
3. Drag a corner to make it big — fill the middle of the page under the cards.
4. With it selected and on the **Build** sub-tab, you'll see wells. (Remember: they may say **"X-axis / Y-axis"** or the older **"Axis / Values"** — same thing.)
5. From the **Data** pane, open `mart_daily_revenue`. Drag **`date_day`** into **X-axis** (or **Axis**). ⚠️ Use **`date_day`** (the calendar date), **not** `date_key` — `date_key` is a number like `20170401`, and Power BI will plot it as "twenty million" on a number line and draw a broken zig-zag instead of a real date trend.
6. From `_Measures`, drag **`GMV (BRL)`** into **Y-axis** (or **Values**).
   *You'll see:* a line that rises over time. ✅
7. Optional: drag **`Merch Revenue (USD)`** into **Y-axis** too, for a second line.

> The left end of the line (2016) looks almost flat — that's **real** (the business was just starting). Leave it.

### Part 3 — revenue by month (column chart)

1. Click empty canvas. Click the **Clustered column chart** icon (vertical bars). Place it bottom-left.
2. Drag **`month_name`** into **X-axis** (Axis), and **`GMV (BRL)`** into **Y-axis** (Values).
3. The months will be in **alphabetical** order (wrong). The chart's own "Sort axis" menu can't fix this, because it only lists fields that are on the chart — and the number column `month` isn't one of them. Instead use the one-time **Sort by column** setting:
   - Go to **Table view** (▦) → in the Data pane open `mart_daily_revenue` → click the **`month_name`** column.
   - On the **Column tools** ribbon → **Sort by column** → choose **`month`**.
   - Back in **Report view**, the chart now runs Jan→Dec. (If not, open the chart's **`…`** menu → **Sort axis** → pick `month_name`, ascending.)
   This is the standard trick for month names, weekday names, or any text with a natural non-alphabetical order — set it once and every chart obeys it.

### Part 4 — weekday vs weekend (column chart)

1. Click empty canvas → **Clustered column chart** icon → place bottom-right.
2. Drag **`is_weekend`** into **X-axis**, and both **`GMV (BRL)`** and **`Orders`** into **Y-axis**.

### Part 5 — slicers (clickable filters)

1. Click empty canvas → click the **Slicer** icon. Place a thin box at the top or side.
2. Drag **`year`** into it.
   *You'll see:* clickable year buttons. ✅
3. Repeat: one slicer for **`quarter`**, one for **`is_weekend`**.

✅ **Page 1 done.** The rest of the pages are the same moves.

---

## Page 2 — Regional Performance

First add the **Page 2 measures** (Phase C method). Make a new page: click the **+** next to the page tabs at the bottom. Rename it `Regional Performance`.

### The map (do the geography fix first!)
1. Power BI needs to be told `state` is a location. Go to **Table view** (▦) → click the `state` column → on **Column tools** ribbon, find **Data category** → choose **State or Province**. Go back to **Report view**.
2. Click empty canvas → **Filled map** icon → place it big.
3. Drag **`state`** into **Location**.
4. Drag **`State GMV (BRL)`** into **Tooltips** (and, if there's a **Legend/Color** well, there too — it shades states by revenue).

> Most of the map will look pale except São Paulo (SP) — that one state is ~40% of all sales. That's real, not a bug.

### Three number cards
- **Card** → `State Orders`
- **Card** → `Avg Delivery Days` *(use this measure, not the raw column)*
- **Card** → `On-Time %` *(use this measure, not the raw column)*

### A leaderboard table
1. **Table** icon → drag these columns in, in order: `state`, `n_orders`, `gmv_brl`, `avg_delivery_days`, `on_time_pct`.
2. (Optional pretty bit) color the on-time column red→green: click the field's dropdown in the well → **Conditional formatting** → **Background color**.

### A scatter chart (slow + unreliable states)
- **Scatter chart** icon → **X-axis** `avg_delivery_days`, **Y-axis** `on_time_pct`, **Size** `n_orders`, **Values/Details** `state`.

### A slicer
- **Slicer** → `state`.

---

## Page 3 — Category Mix

Add **Page 3 measures**. New page → `Category Mix`.

### Top-15 categories (bar chart)
1. **Bar chart** icon (horizontal bars) → **Y-axis** `category`, **X-axis** `Category Revenue (BRL)`.
2. Show only the top 15: in the **Filters** pane (left of Visualizations), find the `category` filter for this chart → change **Filter type** to **Top N** → set **Top** `15` → drag `Category Revenue (BRL)` into the "By value" box → **Apply filter**.

### Two cards
- **Card** → `Categories Tracked`
- **Card** → `Revenue % of Total`

### A treemap (revenue share as nested boxes)
- **Treemap** icon → **Category/Group** `category`, **Values** `Category Revenue (BRL)`.

### A scatter (broad vs valuable categories)
- **Scatter** → **X** `n_products`, **Y** `revenue_brl`, **Size** `n_orders`.

### A detail table + slicer
- **Table** → `category`, `n_orders`, `n_items`, `n_products`, `revenue_brl`, `revenue_usd`.
- **Slicer** → `category`.

---

## Page 4 — Seller Scorecard

Add **Page 4 measures**. New page → `Seller Scorecard`.

### Two cards
- **Card** → `Active Sellers`
- **Card** → `Avg Review Score` *(the measure — not the raw column)*

### The seller leaderboard (table)
- **Table** icon → columns: `seller_id`, `seller_state`, `seller_city`, `n_orders`, `revenue_brl`, `avg_review_score`, `n_reviews`. Click the `revenue_brl` header in the table to sort biggest-first.

### A scatter (high revenue but low rating = risk)
- **Scatter** → **X** `avg_review_score`, **Y** `revenue_brl`, **Size** `n_orders`.

### Sellers per state (column chart)
- **Clustered column** → **X-axis** `seller_state`, **Y-axis** `Active Sellers`.

### Slicers
- **Slicer** → `seller_state`; another **Slicer** → `avg_review_score`.

---

## Page 5 — Customer Retention

Add **Page 5 measures**. New page → `Customer Retention`. (The story of this page: only about **3%** of customers ever come back — that's the real headline.)

### Four cards
- **Card** → `Total Customers`
- **Card** → `Repeat Rate %`
- **Card** → `Avg CLV (BRL)`
- **Card** → `Orders per Customer`

### The main combo chart (new customers + repeat rate over time)
1. **Line and clustered column chart** icon → place big.
2. **X-axis** `cohort_month`.
3. **Column y-axis** `Total Customers`.
4. **Line y-axis** `Repeat Rate %`.

### Repeat rate by month (column chart)
- **Clustered column** → **X-axis** `cohort_month`, **Y-axis** `Repeat Rate %` (the measure).

### Customer value trend (line chart)
- **Line chart** → **X-axis** `cohort_month`, **Y-axis** `Avg CLV (BRL)`.

### Detail table + slicer
- **Table** → `cohort_month`, `n_customers`, `n_repeat_customers`, `repeat_rate_pct`, `avg_orders_per_customer`, `gmv_brl`, `avg_clv_brl`.
- **Slicer** → `cohort_month`.

---

## Make it look nice, then save

1. **Colors:** **View** ribbon → **Themes** → **Customize current theme**. Use green `#1b5e20` for revenue accents and blue `#0d3b66` for headers.
2. **Titles:** **Insert** ribbon → **Text box** → type a title at the top of each page.
3. **Date sliders:** on Page 1 and Page 5, set the date slicers to start **2016-09** and end **2018-10** (the full real data range).
4. **Save:** **File** → **Save As** → navigate to the project's `dashboards` folder → file name `olist_analytics.pbix` → **Save**.

---

## Take screenshots, then tell Claude

1. Press **Win + Shift + S** to start the snipping tool, drag a box around each page, and save the picture. Put the five pictures in the folder `dashboards/screenshots/` with these exact names:
   - `01-executive-overview.png`
   - `02-regional-performance.png`
   - `03-category-mix.png`
   - `04-seller-scorecard.png`
   - `05-customer-retention.png`
2. ⚠️ **Never** screenshot the Snowflake login window (it shows your account name). Only screenshot the finished charts.
3. Tell Claude "the pbix and screenshots are in place" — Claude will save (commit) them and add the pictures to the project's README.

---

## If something looks wrong

| What you see | What's going on / fix |
|---|---|
| A number box shows a giant, silly number | A column wasn't set to **"Don't summarize"** (Phase B). Fix that column, or use the matching **measure** instead of the raw column. |
| I don't see "X-axis / Y-axis" boxes | Click the chart first; make sure the **Build** sub-tab (bar-chart icon, not the paint roller) is active. Cards only show a "Fields" box — that's normal. |
| The map is blank or shows wrong places | You forgot to set `state` → **Data category = State or Province** (Page 2, step 1). |
| Months are in A–Z order, not Jan–Dec | Use the chart's **`…`** menu → **Sort axis** → pick `month`. |
| `ANALYTICS_marts` not in the connect window | Your Snowflake login can't see it — ask for help before continuing. |
| A measure shows a red error | You probably pasted half a line. Delete it and paste a whole line (name + `=` + formula). |
