from django.test import TestCase

from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from coin.models import Strategy, SpinRecord


User = get_user_model()

# ============================================================
# CONFIGURATION
# ============================================================

NUMBER_OF_STRATEGIES = 10
SPINS_PER_STRATEGY = 10

admin = User.objects.filter(is_superuser=True).first()

if not admin:
    admin = User.objects.filter(is_staff=True).first()

if not admin:
    raise Exception(
        "No staff/superuser found. Create an admin user first."
    )


# ============================================================
# ATTRACTIVE AI TRADING STRATEGIES
# ============================================================

strategy_data = [
    {
        "name": "AI Trade Navigator",
        "description": "An AI-assisted trading strategy designed to analyze market trends and identify high-probability opportunities.",
        "short_description": "AI-powered market opportunity strategy.",
        "invested_coin": "multi",
        "strategy_type": "AI Momentum",
        "risk_level": "medium",
        "initial_price": Decimal("15950.00"),
        "min_investment": Decimal("1000.00"),
        "management_fee": Decimal("1.50"),
        "ai_accuracy": Decimal("95.40"),
    },
    {
        "name": "AI Market Pilot",
        "description": "An intelligent trading strategy that uses AI-driven market analysis to help navigate changing market conditions.",
        "short_description": "Smart AI market navigation.",
        "invested_coin": "btc",
        "strategy_type": "AI Momentum",
        "risk_level": "medium",
        "initial_price": Decimal("13925.00"),
        "min_investment": Decimal("3100.00"),
        "management_fee": Decimal("1.50"),
        "ai_accuracy": Decimal("94.80"),
    },
    {
        "name": "AI Profit Navigator",
        "description": "AI-assisted trading technology designed to identify market momentum and potential profit opportunities.",
        "short_description": "AI-assisted profit opportunities.",
        "invested_coin": "multi",
        "strategy_type": "AI Growth",
        "risk_level": "high",
        "initial_price": Decimal("21985.00"),
        "min_investment": Decimal("4150.00"),
        "management_fee": Decimal("1.75"),
        "ai_accuracy": Decimal("96.10"),
    },
    {
        "name": "AI Smart Trader",
        "description": "A smart AI trading strategy that continuously analyzes market activity to support informed trading decisions.",
        "short_description": "Intelligent AI trading strategy.",
        "invested_coin": "eth",
        "strategy_type": "AI Trading",
        "risk_level": "medium",
        "initial_price": Decimal("7910.00"),
        "min_investment": Decimal("900.00"),
        "management_fee": Decimal("1.40"),
        "ai_accuracy": Decimal("95.70"),
    },
    {
        "name": "AI Trend Master",
        "description": "AI-powered trend analysis strategy designed to follow market momentum and react to changing conditions.",
        "short_description": "AI-powered trend following.",
        "invested_coin": "btc",
        "strategy_type": "AI Trend",
        "risk_level": "high",
        "initial_price": Decimal("17975.00"),
        "min_investment": Decimal("1500.00"),
        "management_fee": Decimal("1.90"),
        "ai_accuracy": Decimal("93.90"),
    },
    {
        "name": "AI Wealth Trader",
        "description": "An AI-assisted strategy focused on combining market intelligence with disciplined trading for long-term growth.",
        "short_description": "AI-assisted wealth growth.",
        "invested_coin": "multi",
        "strategy_type": "AI Growth",
        "risk_level": "medium",
        "initial_price": Decimal("30940.00"),
        "min_investment": Decimal("5100.00"),
        "management_fee": Decimal("1.60"),
        "ai_accuracy": Decimal("96.30"),
    },
    {
        "name": "AI Market Hunter",
        "description": "An AI-driven trading strategy built to scan market movements and identify emerging trading opportunities.",
        "short_description": "AI market opportunity scanner.",
        "invested_coin": "multi",
        "strategy_type": "AI Momentum",
        "risk_level": "high",
        "initial_price": Decimal("7995.00"),
        "min_investment": Decimal("2000.00"),
        "management_fee": Decimal("2.00"),
        "ai_accuracy": Decimal("94.20"),
    },
    {
        "name": "AI Trade Vision",
        "description": "A forward-looking AI trading strategy that analyzes market signals to help identify potential opportunities.",
        "short_description": "AI-powered market intelligence.",
        "invested_coin": "eth",
        "strategy_type": "AI Signals",
        "risk_level": "medium",
        "initial_price": Decimal("4965.00"),
        "min_investment": Decimal("1000.00"),
        "management_fee": Decimal("1.55"),
        "ai_accuracy": Decimal("95.90"),
    },
    {
        "name": "AI Momentum Pro",
        "description": "An advanced AI-assisted strategy designed to capture market momentum and respond to significant price movements.",
        "short_description": "Advanced AI momentum trading.",
        "invested_coin": "btc",
        "strategy_type": "AI Momentum",
        "risk_level": "very_high",
        "initial_price": Decimal("11990.00"),
        "min_investment": Decimal("1250.00"),
        "management_fee": Decimal("2.25"),
        "ai_accuracy": Decimal("92.80"),
    },
    {
        "name": "AI Alpha Trader",
        "description": "A premium AI-assisted trading strategy combining market signals, trend analysis and intelligent portfolio positioning.",
        "short_description": "Premium AI trading intelligence.",
        "invested_coin": "multi",
        "strategy_type": "AI Alpha",
        "risk_level": "high",
        "initial_price": Decimal("11000.00"),
        "min_investment": Decimal("2250.00"),
        "management_fee": Decimal("2.10"),
        "ai_accuracy": Decimal("96.50"),
    },
]


# ============================================================
# CREATE STRATEGIES
# ============================================================

now = timezone.now()

for index, data in enumerate(strategy_data):

    strategy, created = Strategy.objects.get_or_create(
        name=data["name"],
        defaults={
            "description": data["description"],
            "short_description": data["short_description"],
            "invested_coin": data["invested_coin"],
            "strategy_type": data["strategy_type"],
            "current_price": data["initial_price"],
            "initial_price": data["initial_price"],
            "min_investment": data["min_investment"],
            "management_fee": data["management_fee"],
            "risk_level": data["risk_level"],
            "ai_accuracy": data["ai_accuracy"],
            "min_holding_period": 6,
            "total_investors": 0,
            "total_invested": Decimal("0.00"),
            "status": "active",
            "is_featured": index < 3,
            "is_public": True,
            "created_by": admin,
        }
    )

    print(
        f"\n{'CREATED' if created else 'EXISTS'}: "
        f"{strategy.name}"
    )

    # Remove old test spin records
    SpinRecord.objects.filter(
        strategy=strategy
    ).delete()

    # Start from original price
    current_price = strategy.initial_price

    # ========================================================
    # CREATE 10 HISTORICAL SPINS
    # ========================================================

    for spin_number in range(1, SPINS_PER_STRATEGY + 1):

        # Alternate UP / DOWN
        if spin_number % 2 == 1:

            action = "spin_up"

            # 1.5% - 3.5% increases
            increases = [
                Decimal("2.10"),
                Decimal("1.80"),
                Decimal("3.20"),
                Decimal("2.40"),
                Decimal("3.50"),
            ]

            percent = increases[(spin_number - 1) // 2]

            new_price = current_price * (
                Decimal("1") + percent / Decimal("100")
            )

        else:

            action = "spin_down"

            # 1% - 2.5% decreases
            decreases = [
                Decimal("1.20"),
                Decimal("1.80"),
                Decimal("1.40"),
                Decimal("2.00"),
                Decimal("1.60"),
            ]

            percent = decreases[(spin_number // 2) - 1]

            new_price = current_price * (
                Decimal("1") - percent / Decimal("100")
            )

        new_price = new_price.quantize(
            Decimal("0.01")
        )

        # ----------------------------------------------------
        # Backdate records
        #
        # Oldest = 45 hours ago
        # Newest = 1 hour ago
        # ----------------------------------------------------

        hours_ago = 45 - ((spin_number - 1) * 5)

        created_time = now - timedelta(
            hours=hours_ago
        )

        spin = SpinRecord.objects.create(
            strategy=strategy,
            admin=admin,
            action=action,
            old_price=current_price,
            new_price=new_price,
            amount_changed=abs(
                new_price - current_price
            ),
            reason=(
                "AI market analysis adjustment"
            ),
            notes=(
                f"Historical AI trading movement #{spin_number}"
            ),
            ip_address=None,
            user_agent="AI Trading Engine",
        )

        # auto_now_add ignores supplied created_at,
        # so update it directly.
        SpinRecord.objects.filter(
            pk=spin.pk
        ).update(
            created_at=created_time
        )

        print(
            f"  {spin_number:02d}. "
            f"{action:<10} "
            f"${current_price:,.2f} → "
            f"${new_price:,.2f} "
            f"({created_time.strftime('%Y-%m-%d %H:%M')})"
        )

        current_price = new_price

    # ========================================================
    # SET FINAL CURRENT PRICE
    # ========================================================

    strategy.current_price = current_price

    strategy.save(
        update_fields=[
            "current_price",
            "updated_at"
        ]
    )

    print(
        f"  FINAL PRICE: ${strategy.current_price:,.2f}"
    )


print("\n" + "=" * 70)
print("AI STRATEGY TEST DATA CREATED")
print("=" * 70)

print(
    f"Strategies: {Strategy.objects.count()}"
)

print(
    f"Spin records: {SpinRecord.objects.count()}"
)

print(
    f"Admin: {admin.username}"
)
