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
N_SESSIONS_TARGET = 375_000  # Target ~350k-400k sessions
N_EVENTS_TARGET = 950_000  # Target between 850k-1M (will be natural result)
N_ORDERS_TARGET = 45_000   # Target between 35k-55k

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

# Bot traffic configuration
BOT_USER_PCT = 0.02  # 2% of users are bots

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

# Product category mapping (deterministic)
PRODUCT_CATEGORIES = ["electronics", "fashion", "home", "beauty", "sports"]


def get_product_category(product_id) -> str:
    """Deterministically assign product category based on product_id."""
    if pd.isna(product_id) or product_id is None:
        return None
    return PRODUCT_CATEGORIES[int(product_id) % len(PRODUCT_CATEGORIES)]


def generate_users() -> pd.DataFrame:
    """
    Generate users table with realistic distributions.
    
    Returns:
        DataFrame with columns: user_id, signup_date, device, country, loyalty_tier
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


def simulate_session_funnel(
    session_id: str,
    user_id: int,
    user_info: Dict,
    start_time: datetime,
) -> List[Dict]:
    """
    Simulate a single session with SESSION-FIRST, FUNNEL-DRIVEN logic.
    
    Each session follows strict funnel progression with increasing timestamps.
    
    Args:
        session_id: Session UUID
        user_id: User ID
        user_info: Dictionary with user attributes (device, country, is_bot, source, loyalty_tier, ab_variant)
        start_time: Session start timestamp
        
    Returns:
        List of event dictionaries in funnel order
    """
    events = []
    current_time = start_time
    is_bot = user_info.get("is_bot", False)
    device = user_info.get("device", "desktop")
    source = user_info.get("source", "organic")
    loyalty_tier = user_info.get("loyalty_tier", "bronze")
    ab_variant = user_info.get("ab_variant", "control")
    
    # Stage 1: Visit (ALWAYS exactly once)
    events.append({
        "event_id": str(uuid.uuid4()),
        "user_id": user_id,
        "session_id": session_id,
        "event_type": "visit",
        "page": "home",
        "product_id": None,
        "product_category": None,
        "ts": current_time,
        "source": source,
        "device": device,
        "ab_test_id": None,
        "variant": None
    })
    current_time += timedelta(seconds=np.random.exponential(30))
    
    # Stage 2: Product View (Probability: 0.75-0.85)
    product_view_prob = np.random.uniform(0.75, 0.85)
    viewed_products = []
    
    if np.random.random() < product_view_prob:
        # 1-4 product views per session
        n_views = np.random.poisson(2.5) + 1
        n_views = min(n_views, 4)  # Cap at 4
        
        for i in range(n_views):
            product_id = np.random.randint(1, N_PRODUCTS + 1)
            viewed_products.append(product_id)
            events.append({
                "event_id": str(uuid.uuid4()),
                "user_id": user_id,
                "session_id": session_id,
                "event_type": "product_view",
                "page": "product",
                "product_id": product_id,
                "product_category": get_product_category(product_id),
                "ts": current_time + timedelta(seconds=i*10 + np.random.exponential(15)),
                "source": source,
                "device": device,
                "ab_test_id": None,
                "variant": None
            })
        current_time += timedelta(seconds=np.random.exponential(60))
    
    # Bots never proceed past product_view
    if is_bot:
        return events
    
    # Stage 3: Add to Cart (CONDITIONAL on product_view, Probability: 0.30-0.40)
    if viewed_products:
        add_to_cart_prob = np.random.uniform(0.30, 0.40)
        
        # Higher for gold/platinum users
        if loyalty_tier in ["gold", "platinum"]:
            add_to_cart_prob = min(0.40, add_to_cart_prob * 1.15)
        
        if np.random.random() < add_to_cart_prob:
            # Add 1-3 products to cart
            n_cart_items = min(np.random.poisson(1.5) + 1, len(viewed_products))
            cart_products = []
            
            for i in range(n_cart_items):
                product_id = np.random.choice(viewed_products)
                cart_products.append(product_id)
                events.append({
                    "event_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "session_id": session_id,
                    "event_type": "add_to_cart",
                    "page": "product",
                    "product_id": product_id,
                    "product_category": get_product_category(product_id),
                    "ts": current_time + timedelta(seconds=i*5 + np.random.exponential(10)),
                    "source": source,
                    "device": device,
                    "ab_test_id": None,
                    "variant": None
                })
            current_time += timedelta(seconds=np.random.exponential(45))
            
            # Stage 4: Checkout (CONDITIONAL on add_to_cart, Probability: 0.45-0.55)
            checkout_prob = np.random.uniform(0.45, 0.55)
            
            # Slightly lower for mobile
            if device == "mobile":
                checkout_prob *= 0.95  # 5% reduction
            
            if np.random.random() < checkout_prob:
                events.append({
                    "event_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "session_id": session_id,
                    "event_type": "checkout",
                    "page": "checkout",
                    "product_id": None,
                    "product_category": None,
                    "ts": current_time,
                    "source": source,
                    "device": device,
                    "ab_test_id": "checkout_layout_test_1",
                    "variant": ab_variant
                })
                current_time += timedelta(seconds=np.random.exponential(120))
                
                # Stage 5: Purchase (CONDITIONAL on checkout)
                # Control: ~0.85, Variant: ~0.92
                purchase_prob = 0.85 if ab_variant == "control" else 0.92
                
                if np.random.random() < purchase_prob:
                    # Purchase primary product from cart
                    product_id = cart_products[0]
                    events.append({
                        "event_id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "session_id": session_id,
                        "event_type": "purchase",
                        "page": "checkout",
                        "product_id": product_id,
                        "product_category": get_product_category(product_id),
                        "ts": current_time,
                        "source": source,
                        "device": device,
                        "ab_test_id": "checkout_layout_test_1",
                        "variant": ab_variant
                    })
    
    return events


def generate_events(users_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate events table using SESSION-FIRST, FUNNEL-DRIVEN approach.
    
    First generates ~350k-400k sessions, then creates events for each session
    following strict funnel progression.
    
    Args:
        users_df: Users dataframe
        
    Returns:
        DataFrame with event columns
    """
    print("\nGenerating events (SESSION-FIRST approach)...")
    
    user_info_dict = users_df.set_index("user_id").to_dict("index")
    
    # Step 1: Generate sessions first
    print(f"  Step 1: Generating ~{N_SESSIONS_TARGET:,} sessions...")
    sessions = []
    
    # Assign A/B test variant deterministically at user level
    for user_id in users_df["user_id"]:
        user_info = user_info_dict[user_id]
        user_info["ab_variant"] = "variant" if (int(user_id) % 2 == 0) else "control"
    
    # Generate sessions for each user
    for user_id in users_df["user_id"]:
        user_info = user_info_dict[user_id]
        is_bot = user_info["is_bot"]
        loyalty_tier = user_info.get("loyalty_tier", "bronze")
        
        # Determine number of sessions per user
        if is_bot:
            # Bots have many sessions
            n_sessions = np.random.poisson(15) + 10
        else:
            # Regular users: session count influenced by loyalty tier
            if loyalty_tier == "platinum":
                lambda_sessions = 4.5
            elif loyalty_tier == "gold":
                lambda_sessions = 3.5
            elif loyalty_tier == "silver":
                lambda_sessions = 2.5
            else:  # bronze
                lambda_sessions = 1.8
            n_sessions = np.random.poisson(lambda_sessions) + 1
        
        # Generate sessions for this user
        signup_date = user_info["signup_date"]
        for _ in range(n_sessions):
            # Session start time (after signup, weighted toward recent)
            days_since_signup = np.random.exponential(30)
            session_start = signup_date + timedelta(days=int(days_since_signup))
            session_start = min(session_start, END_DATE)
            
            # Assign traffic source
            if np.random.random() < SOURCE_PROBS[1]:  # paid
                source = "paid"
            else:
                remaining_probs = [SOURCE_PROBS[0], SOURCE_PROBS[2], SOURCE_PROBS[3]]
                remaining_probs = np.array(remaining_probs) / sum(remaining_probs)
                remaining_sources = ["organic", "email", "referral"]
                source = np.random.choice(remaining_sources, p=remaining_probs)
            
            sessions.append({
                "session_id": generate_session_id(),
                "user_id": user_id,
                "start_time": session_start,
                "source": source
            })
    
    # Trim to target if needed (convert to list first for random choice)
    if len(sessions) > N_SESSIONS_TARGET * 1.1:
        indices = np.random.choice(len(sessions), size=int(N_SESSIONS_TARGET * 1.05), replace=False)
        sessions = [sessions[i] for i in indices]
    
    print(f"  Generated {len(sessions):,} sessions")
    
    # Step 2: Generate events for each session
    print(f"  Step 2: Generating events for each session...")
    all_events = []
    
    for session in sessions:
        user_id = session["user_id"]
        user_info = user_info_dict[user_id].copy()
        user_info["source"] = session["source"]
        
        session_events = simulate_session_funnel(
            session_id=session["session_id"],
            user_id=user_id,
            user_info=user_info,
            start_time=session["start_time"]
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
        duplicate_indices = events_df[duplicate_mask].index
        source_indices = np.random.choice(events_df[~duplicate_mask].index, size=len(duplicate_indices))
        events_df.loc[duplicate_indices, "session_id"] = events_df.loc[source_indices, "session_id"].values
    
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
        return pd.DataFrame(columns=["order_id", "user_id", "product_id", "price", "quantity", "discount_amount", "ts", "payment_status"])
    
    print(f"  Found {len(purchase_events):,} purchase events")
    
    # Generate orders
    orders = []
    for _, event in purchase_events.iterrows():
        # Generate order ID
        order_id = str(uuid.uuid4())
        
        # Generate price (lognormal distribution)
        log_price = np.random.normal(PRICE_LOG_MEAN, PRICE_LOG_STD)
        price = np.exp(log_price)
        price = np.clip(price, MIN_PRICE, MAX_PRICE)
        price = round(price, 2)
        
        # Quantity (1-4, skewed toward 1)
        quantity = np.random.choice([1, 2, 3, 4], p=[0.70, 0.20, 0.07, 0.03])
        
        # Discount amount (mostly 0, higher for paid traffic and variant users)
        discount_amount = 0.0
        if event["source"] == "paid" or event.get("variant") == "variant":
            if np.random.random() < 0.15:  # 15% chance of discount
                discount_amount = round(price * np.random.uniform(0.05, 0.20), 2)
        
        # Ensure price - discount >= MIN_PRICE
        if price - discount_amount < MIN_PRICE:
            discount_amount = max(0, price - MIN_PRICE)
        
        # Payment status (8% failure rate)
        payment_status = "failed" if np.random.random() < 0.08 else "success"
        
        orders.append({
            "order_id": order_id,
            "user_id": event["user_id"],
            "product_id": event["product_id"],
            "price": price,
            "quantity": quantity,
            "discount_amount": discount_amount,
            "ts": event["ts"],
            "payment_status": payment_status
        })
    
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
    
    # Session count
    total_sessions = events_df["session_id"].nunique()
    print(f"  Total Sessions: {total_sessions:,}")
    
    print(f"\nFunnel Drop-off Analysis:")
    event_counts = events_df["event_type"].value_counts().sort_index()
    for event_type in ["visit", "product_view", "add_to_cart", "checkout", "purchase"]:
        count = event_counts.get(event_type, 0)
        pct = (count / len(events_df) * 100) if len(events_df) > 0 else 0
        print(f"  {event_type:15s}: {count:8,} ({pct:5.2f}%)")
    
    # Calculate conversion rates (session-level)
    print(f"\nFunnel Conversion Rates (Session-level):")
    
    sessions_with_product_view = events_df[events_df["event_type"] == "product_view"]["session_id"].nunique()
    sessions_with_add_to_cart = events_df[events_df["event_type"] == "add_to_cart"]["session_id"].nunique()
    sessions_with_checkout = events_df[events_df["event_type"] == "checkout"]["session_id"].nunique()
    sessions_with_purchase = events_df[events_df["event_type"] == "purchase"]["session_id"].nunique()
    
    if sessions_with_product_view > 0:
        conv_rate = (sessions_with_add_to_cart / sessions_with_product_view) * 100
        print(f"  Product View -> Add Cart:  {conv_rate:.2f}% ({sessions_with_add_to_cart:,} / {sessions_with_product_view:,} sessions)")
    
    if sessions_with_add_to_cart > 0:
        conv_rate = (sessions_with_checkout / sessions_with_add_to_cart) * 100
        print(f"  Add Cart -> Checkout:      {conv_rate:.2f}% ({sessions_with_checkout:,} / {sessions_with_add_to_cart:,} sessions)")
    
    if sessions_with_checkout > 0:
        conv_rate = (sessions_with_purchase / sessions_with_checkout) * 100
        print(f"  Checkout -> Purchase:      {conv_rate:.2f}% ({sessions_with_purchase:,} / {sessions_with_checkout:,} sessions)")
    
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
        print(f"  Total Revenue:       ${orders_df[orders_df['payment_status'] == 'success']['price'].sum():,.2f}")

        # Orders by product_category
        print(f"\nOrders by Product Category:")
        order_categories = orders_df["product_id"].apply(lambda x: get_product_category(x) if pd.notna(x) else None)
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
    print("E-COMMERCE DATA GENERATOR (SESSION-FIRST)")
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
