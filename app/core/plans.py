SUBSCRIPTION_PLANS = {
    "starter": {
        "plan_id": "plan_RY28EDrIpxnSjb",
        "name": "Starter",
        "price": 3999,
        "rfp_limit": 10,
        "doc_limit": 50,
    },
    "growth": {
        "plan_id": "plan_RY28qIQoiKhR1s",
        "name": "Growth", 
        "price": 7999,
        "rfp_limit": 25,
        "doc_limit": 150,
    },
    "pro": {
        "plan_id": "plan_RY29PU7dxni8n7",
        "name": "Pro",
        "price": 15999,
        "rfp_limit": 100,
        "doc_limit": 500,
    },
    "free": {
        "plan_id": None,
        "name": "Free",
        "price": 0,
        "rfp_limit": 2,
        "doc_limit": 10,
    }
}

def get_plan_config(tier: str):
    """Get configuration for a subscription tier"""
    return SUBSCRIPTION_PLANS.get(tier, SUBSCRIPTION_PLANS["free"])