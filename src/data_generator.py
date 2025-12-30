"""
E-commerce Product Analytics - Data Generator

Generates realistic e-commerce clickstream and order data with intentional noise
to simulate real-world data challenges.

Usage:
    python src/data_generator.py

Output:
    - data/raw/users.csv
    - data/raw/events.csv
    - data/raw/orders.csv
"""

import os
import uuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, List, Dict


# Configuration
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Data scale
N_USERS = 120_000
N_EVENTS_TARGET = 950_000  # Target between 850k-1M
N_ORDERS_TARGET = 50_000   # Target between 40k-60k

# Output directory
OUTPUT_DIR = "data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Distributions
DEVICE_DIST = ["mobile", "desktop", "tablet"]
DEVICE_PROBS = [0.65, 0.30, 0.05]

COUNTRIES = ["US", "IN", "UK", "DE", "AU"]
COUNTRY_PROBS = [0.40, 0.25, 0.15, 0.12, 0.08]  # US-heavy distribution

SOURCES = ["organic", "paid", "email", "referral"]
SOURCE_PROBS = [0.45, 0.35, 0.12, 0.08]  # Paid traffic higher volume

# Funnel probabilities (conditional)
# visit -> product_view -> add_to_cart -> checkout -> purchase
FUNNEL_PROBS = {
    "visit": 1.0,                    # 100% start with visit
    "product_view": 0.75,            # 75% of visits view products
    "add_to_cart": 0.40,            # 40% of product views add to cart
    "checkout": 0.30,               # 30% of add_to_cart reach checkout (70% abandonment)
    "purchase": 0.92,               # 92% of checkouts complete purchase (8% payment failure)
}

# Bot traffic configuration
BOT_USER_PCT = 0.02  # 2% of users are bots
BOT_EVENTS_MULTIPLIER = 50  # Bots generate 50x more events
BOT_PURCHASE_PROB = 0.0  # Bots never purchase

# Other noise parameters
MISSING_SESSION_PCT = 0.03  # 3% of events missing session_id
DUPLICATE_SESSION_PCT = 0.01  # 1% chance of duplicate session_id

# Time range
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)
DATE_RANGE_DAYS = (END_DATE - START_DATE).days

# Product configuration
N_PRODUCTS = 2000
MIN_PRICE = 9.99
MAX_PRICE = 999.99
PRICE_LOG_MEAN = 3.5  # lognormal mean
PRICE_LOG_STD = 0.8   # lognormal std

# Product categories (dimension)
PRODUCT_CATEGORIES = ["electronics", "fashion", "home", "beauty", "sports"]


def get_product_category(product_id: int | None) -> str | None:
    """
    Deterministically map a product_id to a product_category.

    We use a simple modulo-based mapping so each product_id is always
    assigned the same category without needing an external table.
    """
    if product_id is None:
        return None
    idx = (int(product_id) - 1) % len(PRODUCT_CATEGORIES)
    return PRODUCT_CATEGORIES[idx]


def generate_users() -> pd.DataFrame:
    """
    Generate users table with realistic distributions.
    
    Returns:
        DataFrame with columns: user_id, signup_date, device, country
    """
    print("Generating users...")
    
    # Generate user IDs
    user_ids = np.arange(1, N_USERS + 1)
    
    # Generate signup dates (more recent signups slightly more common)
    # Using beta distribution to create slight bias toward recent dates
    signup_days = np.random.beta(2, 3, N_USERS) * DATE_RANGE_DAYS
    signup_dates = [START_DATE + timedelta(days=int(d)) for d in signup_days]
    
    # Generate devices with specified distribution
    devices = np.random.choice(DEVICE_DIST, size=N_USERS, p=DEVICE_PROBS)
    
    # Generate countries with specified distribution
    countries = np.random.choice(COUNTRIES, size=N_USERS, p=COUNTRY_PROBS)
    
    # Identify bot users (2% of users)
    is_bot = np.random.random(N_USERS) < BOT_USER_PCT

    users_df = pd.DataFrame({
        "user_id": user_ids,
        "signup_date": signup_dates,
        "device": devices,
        "country": countries,
        "is_bot": is_bot  # Internal flag, will be removed before saving
    })

    # Assign loyalty tiers based on signup recency (earlier signup → higher tier)
    # Target distribution (approx):
    # - bronze  ~60%
    # - silver  ~25%
    # - gold    ~12%
    # - platinum ~3%
    users_sorted = users_df.sort_values("signup_date").copy()
    n = len(users_sorted)
    n_platinum = int(0.03 * n)
    n_gold = int(0.12 * n)
    n_silver = int(0.25 * n)
    # Remaining users will be bronze

    loyalty_tier = np.full(n, "bronze", dtype=object)
    # Earliest signups get higher tiers
    loyalty_tier[: n_platinum] = "platinum"
    loyalty_tier[n_platinum : n_platinum + n_gold] = "gold"
    loyalty_tier[n_platinum + n_gold : n_platinum + n_gold + n_silver] = "silver"
    users_sorted["loyalty_tier"] = loyalty_tier

    # Map back to original order
    users_df = (
        users_sorted[["user_id", "signup_date", "device", "country", "is_bot", "loyalty_tier"]]
        .sort_values("user_id")
        .reset_index(drop=True)
    )

    print(f"  Generated {len(users_df)} users")
    print(f"  Bot users: {is_bot.sum()} ({is_bot.sum()/len(users_df)*100:.2f}%)")
    print("  Loyalty distribution:")
    loyalty_counts = users_df["loyalty_tier"].value_counts()
    for tier, cnt in loyalty_counts.items():
        print(f"    {tier:8s}: {cnt:8,} ({cnt/len(users_df)*100:5.2f}%)")
    
    return users_df


def generate_session_id() -> str:
    """Generate a UUID session ID."""
    return str(uuid.uuid4())


def simulate_user_session(
    user_id: int,
    user_info: Dict,
    start_time: datetime,
    funnel_probs: Dict[str, float],
) -> List[Dict]:
    """
    Simulate a single user session with realistic funnel progression.
    
    Args:
        user_id: User ID
        user_info: Dictionary with user attributes (device, country, is_bot, source)
        start_time: Session start timestamp
        
    Returns:
        List of event dictionaries
    """
    events = []
    current_time = start_time
    session_id = generate_session_id()
    
    # Determine if this is a bot session
    is_bot = user_info.get("is_bot", False)
    
    # Bot sessions: many events, no purchases
    if is_bot:
        n_events = np.random.poisson(50)  # Bots generate many events
        event_types = ["visit", "product_view"]  # Bots only browse
        for i in range(n_events):
            event_type = np.random.choice(event_types)
            events.append({
                "event_id": str(uuid.uuid4()),
                "user_id": user_id,
                "session_id": session_id,
                "event_type": event_type,
                "page": "product" if event_type == "product_view" else "home",
                "product_id": np.random.randint(1, N_PRODUCTS + 1),
                "ts": current_time + timedelta(seconds=i*5),
                "source": user_info.get("source", "organic"),
                "device": user_info.get("device", "desktop")
            })
        return events
    
    # Regular user session - follow funnel
    # Stage 1: Visit
    if np.random.random() < funnel_probs["visit"]:
        events.append({
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": session_id,
            "event_type": "visit",
            "page": "home",
            "product_id": None,
            "ts": current_time,
            "source": user_info.get("source", "organic"),
            "device": user_info.get("device", "desktop")
        })
        current_time += timedelta(seconds=np.random.exponential(30))
    
    # Stage 2: Product View
    if events and np.random.random() < funnel_probs["product_view"]:
        n_views = np.random.poisson(3) + 1  # 1-4 product views typically
        for i in range(n_views):
            product_id = np.random.randint(1, N_PRODUCTS + 1)
            events.append({
                "event_id": str(uuid.uuid4()),
                "user_id": user_id,
                "session_id": session_id,
                "event_type": "product_view",
                "page": "product",
                "product_id": product_id,
                "product_category": get_product_category(product_id),
                "ts": current_time + timedelta(seconds=i*10),
                "source": user_info.get("source", "organic"),
                "device": user_info.get("device", "desktop")
            })
        current_time += timedelta(seconds=np.random.exponential(60))
    
    # Stage 3: Add to Cart
    if len(events) > 1 and np.random.random() < funnel_probs["add_to_cart"]:
        # Add 1-3 products to cart
        n_cart_items = np.random.poisson(1.5) + 1
        viewed_products = [e["product_id"] for e in events if e["event_type"] == "product_view"]
        for i in range(min(n_cart_items, len(viewed_products))):
            product_id = (
                np.random.choice(viewed_products)
                if viewed_products
                else np.random.randint(1, N_PRODUCTS + 1)
            )
            events.append({
                "event_id": str(uuid.uuid4()),
                "user_id": user_id,
                "session_id": session_id,
                "event_type": "add_to_cart",
                "page": "product",
                "product_id": product_id,
                "product_category": get_product_category(product_id),
                "ts": current_time + timedelta(seconds=i*5),
                "source": user_info.get("source", "organic"),
                "device": user_info.get("device", "desktop")
            })
        current_time += timedelta(seconds=np.random.exponential(45))
    
    # Stage 4: Checkout
    if any(e["event_type"] == "add_to_cart" for e in events) and np.random.random() < funnel_probs["checkout"]:
        event = {
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": session_id,
            "event_type": "checkout",
            "page": "checkout",
            "product_id": None,
            "product_category": None,
            "ts": current_time,
            "source": user_info.get("source", "organic"),
            "device": user_info.get("device", "desktop")
        }
        # Attach A/B test metadata for checkout events
        ab_variant = user_info.get("ab_variant")
        if ab_variant is not None:
            event["ab_test_id"] = "checkout_layout_test_1"
            event["variant"] = ab_variant
        events.append(event)
        current_time += timedelta(seconds=np.random.exponential(120))
    
    # Stage 5: Purchase
    if any(e["event_type"] == "checkout" for e in events) and np.random.random() < funnel_probs["purchase"]:
        # Get products from cart
        cart_products = [e["product_id"] for e in events if e["event_type"] == "add_to_cart"]
        if cart_products:
            product_id = cart_products[0]
            event = {
                "event_id": str(uuid.uuid4()),
                "user_id": user_id,
                "session_id": session_id,
                "event_type": "purchase",
                "page": "checkout",
                "product_id": product_id,  # Primary product
                "product_category": get_product_category(product_id),
                "ts": current_time,
                "source": user_info.get("source", "organic"),
                "device": user_info.get("device", "desktop")
            }
            ab_variant = user_info.get("ab_variant")
            if ab_variant is not None:
                event["ab_test_id"] = "checkout_layout_test_1"
                event["variant"] = ab_variant
            events.append(event)
    
    return events


def generate_events(users_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate events table with realistic funnel behavior and noise.
    
    Args:
        users_df: Users dataframe
        
    Returns:
        DataFrame with event columns
    """
    print("\nGenerating events...")
    
    all_events = []
    user_info_dict = users_df.set_index("user_id").to_dict("index")
    
    # Calculate target events per user (adjusting for bots)
    n_regular_users = (~users_df["is_bot"]).sum()
    n_bot_users = users_df["is_bot"].sum()
    
    # Regular users generate ~8 events on average
    # Bot users generate ~50x more
    regular_events_per_user = (N_EVENTS_TARGET - (n_bot_users * 50 * 8)) / n_regular_users
    regular_events_per_user = max(1, int(regular_events_per_user))
    
    print(f"  Target events: {N_EVENTS_TARGET:,}")
    print(f"  Regular users: {n_regular_users:,} (~{regular_events_per_user} events/user)")
    print(f"  Bot users: {n_bot_users:,} (~{regular_events_per_user * BOT_EVENTS_MULTIPLIER} events/user)")
    
    # Generate events for each user
    for user_id in users_df["user_id"]:
        user_info = user_info_dict[user_id]
        is_bot = user_info["is_bot"]

        # Determine A/B test variant deterministically at user level
        ab_variant = "variant" if (int(user_id) % 2 == 0) else "control"
        user_info["ab_variant"] = ab_variant

        # Determine number of sessions for this user
        if is_bot:
            n_sessions = np.random.poisson(10) + 5  # Bots have many sessions
        else:
            # Regular users: session count influenced by loyalty tier
            loyalty = user_info.get("loyalty_tier", "bronze")
            if loyalty == "platinum":
                lambda_sessions = 4.0
            elif loyalty == "gold":
                lambda_sessions = 3.0
            elif loyalty == "silver":
                lambda_sessions = 2.0
            else:  # bronze
                lambda_sessions = 1.5
            n_sessions = np.random.poisson(lambda_sessions) + 1
        
        # Generate sessions
        signup_date = user_info["signup_date"]
        for session_num in range(n_sessions):
            # Session start time (after signup, weighted toward recent)
            days_since_signup = np.random.exponential(30)
            session_start = signup_date + timedelta(days=int(days_since_signup))
            session_start = min(session_start, END_DATE)
            
            # Assign traffic source (paid traffic has lower conversion)
            if np.random.random() < SOURCE_PROBS[1]:  # paid
                source = "paid"
                # Paid traffic: slightly lower conversion rates
                funnel_probs_session = {k: v * 0.85 for k, v in FUNNEL_PROBS.items()}
            else:
                # Normalize remaining probabilities (excluding paid)
                remaining_probs = [SOURCE_PROBS[0], SOURCE_PROBS[2], SOURCE_PROBS[3]]
                remaining_probs = np.array(remaining_probs) / sum(remaining_probs)
                remaining_sources = ["organic", "email", "referral"]
                source = np.random.choice(remaining_sources, p=remaining_probs)
                funnel_probs_session = FUNNEL_PROBS.copy()

            # Variant uplift: slightly higher purchase probability
            if not is_bot and ab_variant == "variant":
                funnel_probs_session["purchase"] = min(
                    1.0, funnel_probs_session["purchase"] * 1.05
                )

            user_info_with_source = {
                **user_info,
                "source": source,
                "ab_variant": ab_variant,
            }

            # Generate session events
            session_events = simulate_user_session(
                user_id, user_info_with_source, session_start, funnel_probs_session
            )
            all_events.extend(session_events)
    
    # Convert to DataFrame
    events_df = pd.DataFrame(all_events)
    
    # Add noise: missing session_ids (~3%)
    missing_mask = np.random.random(len(events_df)) < MISSING_SESSION_PCT
    events_df.loc[missing_mask, "session_id"] = None
    
    # Add noise: duplicate session_ids (~1%)
    duplicate_mask = np.random.random(len(events_df)) < DUPLICATE_SESSION_PCT
    if duplicate_mask.sum() > 0:
        # Copy session_ids from random existing events
        duplicate_indices = events_df[duplicate_mask].index
        source_indices = np.random.choice(events_df[~duplicate_mask].index, size=len(duplicate_indices))
        events_df.loc[duplicate_indices, "session_id"] = events_df.loc[source_indices, "session_id"].values
    
    # Ensure we're close to target (trim if needed)
    if len(events_df) > N_EVENTS_TARGET * 1.1:
        events_df = events_df.sample(n=int(N_EVENTS_TARGET * 1.05), random_state=RANDOM_SEED).sort_values("ts")
    
    print(f"  Generated {len(events_df):,} events")
    
    return events_df


def generate_orders(events_df: pd.DataFrame, users_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate orders table from purchase events.
    
    Args:
        events_df: Events dataframe
        users_df: Users dataframe
        
    Returns:
        DataFrame with order columns
    """
    print("\nGenerating orders...")
    
    # Get purchase events
    purchase_events = events_df[events_df["event_type"] == "purchase"].copy()
    
    if len(purchase_events) == 0:
        print("  Warning: No purchase events found!")
        return pd.DataFrame(columns=["order_id", "user_id", "product_id", "price", "ts", "payment_status"])
    
    print(f"  Found {len(purchase_events):,} purchase events")
    
    # Generate orders
    orders = []
    for _, event in purchase_events.iterrows():
        # Generate order ID
        order_id = str(uuid.uuid4())

        # Generate base unit price (lognormal distribution)
        log_price = np.random.normal(PRICE_LOG_MEAN, PRICE_LOG_STD)
        unit_price = np.exp(log_price)
        unit_price = np.clip(unit_price, MIN_PRICE, MAX_PRICE)
        unit_price = round(unit_price, 2)

        # Quantity: 1–4, skewed toward 1
        quantities = np.array([1, 2, 3, 4])
        quantity_probs = np.array([0.7, 0.2, 0.07, 0.03])
        quantity = int(np.random.choice(quantities, p=quantity_probs))

        # Base total before discounts
        base_total = unit_price * quantity

        # Discount logic
        discount_amount = 0.0
        source = event.get("source", "organic")
        variant = event.get("variant", "control")

        eligible_for_discount = (source == "paid") or (variant == "variant")
        if eligible_for_discount and np.random.random() < 0.4:
            # 5–25% discount, capped so final price stays realistic
            discount_pct = np.random.uniform(0.05, 0.25)
            discount_amount = round(base_total * discount_pct, 2)
            # Ensure final price is not below MIN_PRICE
            if base_total - discount_amount < MIN_PRICE:
                discount_amount = max(0.0, base_total - MIN_PRICE)

        final_price = round(base_total - discount_amount, 2)

        # Payment status (8% failure rate)
        payment_status = "failed" if np.random.random() < 0.08 else "success"

        orders.append(
            {
                "order_id": order_id,
                "user_id": event["user_id"],
                "product_id": event["product_id"],
                "price": final_price,
                "quantity": quantity,
                "discount_amount": discount_amount,
                "ts": event["ts"],
                "payment_status": payment_status,
            }
        )
    
    orders_df = pd.DataFrame(orders)

    print(f"  Generated {len(orders_df):,} orders")
    print(f"  Successful payments: {(orders_df['payment_status'] == 'success').sum():,}")
    print(f"  Failed payments: {(orders_df['payment_status'] == 'failed').sum():,}")
    
    return orders_df


def validate_and_print_stats(users_df: pd.DataFrame, events_df: pd.DataFrame, orders_df: pd.DataFrame):
    """Print validation statistics."""
    print("\n" + "="*60)
    print("VALIDATION STATISTICS")
    print("="*60)
    
    print(f"\nRow Counts:")
    print(f"  Users: {len(users_df):,}")
    print(f"  Events: {len(events_df):,}")
    print(f"  Orders: {len(orders_df):,}")

    # Loyalty tier distribution
    print(f"\nLoyalty Tier Distribution:")
    if "loyalty_tier" in users_df.columns:
        loyalty_counts = users_df["loyalty_tier"].value_counts()
        for tier, count in loyalty_counts.items():
            print(f"  {tier:8s}: {count:8,} ({count/len(users_df)*100:5.2f}%)")
    
    print(f"\nFunnel Drop-off Analysis:")
    event_counts = events_df["event_type"].value_counts().sort_index()
    for event_type in ["visit", "product_view", "add_to_cart", "checkout", "purchase"]:
        count = event_counts.get(event_type, 0)
        pct = (count / len(events_df) * 100) if len(events_df) > 0 else 0
        print(f"  {event_type:15s}: {count:8,} ({pct:5.2f}%)")
    
    # Calculate conversion rates
    if "visit" in event_counts:
        visits = event_counts["visit"]
        print(f"\nConversion Rates:")
        print(
            f"  Visit -> Product View:     "
            f"{event_counts.get('product_view', 0)/visits*100:.2f}%"
        )
        print(
            f"  Product View -> Add Cart:  "
            f"{event_counts.get('add_to_cart', 0)/event_counts.get('product_view', 1)*100:.2f}%"
        )
        print(
            f"  Add Cart -> Checkout:      "
            f"{event_counts.get('checkout', 0)/event_counts.get('add_to_cart', 1)*100:.2f}%"
        )
        print(
            f"  Checkout -> Purchase:      "
            f"{event_counts.get('purchase', 0)/event_counts.get('checkout', 1)*100:.2f}%"
        )
    
    print(f"\nDevice Distribution:")
    device_counts = events_df["device"].value_counts()
    for device, count in device_counts.items():
        print(f"  {device:10s}: {count:8,} ({count/len(events_df)*100:5.2f}%)")
    
    print(f"\nSource Distribution:")
    source_counts = events_df["source"].value_counts()
    for source, count in source_counts.items():
        print(f"  {source:10s}: {count:8,} ({count/len(events_df)*100:5.2f}%)")
    
    print(f"\nOrder Statistics:")
    if len(orders_df) > 0:
        print(f"  Average Order Value: ${orders_df['price'].mean():.2f}")
        print(f"  Median Order Value:  ${orders_df['price'].median():.2f}")
        print(
            f"  Total Revenue:       "
            f"${orders_df[orders_df['payment_status'] == 'success']['price'].sum():,.2f}"
        )

        # Orders by product_category
        print(f"\nOrders by Product Category:")
        # Derive category from product_id using the same deterministic mapping
        order_categories = orders_df["product_id"].apply(get_product_category)
        category_counts = order_categories.value_counts()
        for cat, count in category_counts.items():
            print(f"  {cat:10s}: {count:8,} ({count/len(orders_df)*100:5.2f}%)")

        # Conversion rate: control vs variant (checkout -> purchase)
        print(f"\nA/B Test Conversion (Checkout -> Purchase):")
        ab_events = events_df[
            events_df["event_type"].isin(["checkout", "purchase"])
        ].copy()
        if "variant" in ab_events.columns:
            for variant in ["control", "variant"]:
                checkout_mask = (ab_events["event_type"] == "checkout") & (
                    ab_events.get("variant") == variant
                )
                purchase_mask = (ab_events["event_type"] == "purchase") & (
                    ab_events.get("variant") == variant
                )
                checkouts = checkout_mask.sum()
                purchases = purchase_mask.sum()
                conv_rate = (purchases / checkouts * 100) if checkouts > 0 else 0.0
                print(
                    f"  {variant:8s}: "
                    f"checkouts={checkouts:6,}, purchases={purchases:6,}, "
                    f"conversion={conv_rate:5.2f}%"
                )
    
    print(f"\nData Quality Checks:")
    missing_sessions = events_df["session_id"].isna().sum()
    print(f"  Missing session_ids: {missing_sessions:,} ({missing_sessions/len(events_df)*100:.2f}%)")
    
    print("\n" + "="*60)


def main():
    """Main execution function."""
    print("="*60)
    print("E-COMMERCE DATA GENERATOR")
    print("="*60)
    print(f"Random Seed: {RANDOM_SEED}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("="*60)
    
    # Generate data
    users_df = generate_users()
    events_df = generate_events(users_df)
    orders_df = generate_orders(events_df, users_df)
    
    # Remove internal columns before saving
    users_export = users_df.drop(columns=["is_bot"])
    
    # Save to CSV
    print("\nSaving files...")
    users_export.to_csv(f"{OUTPUT_DIR}/users.csv", index=False)
    print(f"  [OK] Saved {OUTPUT_DIR}/users.csv")
    
    events_df.to_csv(f"{OUTPUT_DIR}/events.csv", index=False)
    print(f"  [OK] Saved {OUTPUT_DIR}/events.csv")
    
    orders_df.to_csv(f"{OUTPUT_DIR}/orders.csv", index=False)
    print(f"  [OK] Saved {OUTPUT_DIR}/orders.csv")
    
    # Validation
    validate_and_print_stats(users_export, events_df, orders_df)

    print("\n[SUCCESS] Data generation complete!")
    print(f"Files saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

