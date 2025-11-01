SUBSCRIPTION_PLANS = {
    "starter": {
        "plan_id": "plan_RY41A8qKz1MgSw",
        "name": "Starter",
        "price": 49,
        "rfp_limit": 10,
        "doc_limit": 50,
    },
    "growth": {
        "plan_id": "plan_RY41P3CLgQpHA6",
        "name": "Growth", 
        "price": 99,
        "rfp_limit": 25,
        "doc_limit": 150,
    },
    "pro": {
        "plan_id": "plan_RY41dLUizZQvpP",
        "name": "Pro",
        "price": 199,
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
    return SUBSCRIPTION_PLANS.get(tier, SUBSCRIPTION_PLANS["free"])