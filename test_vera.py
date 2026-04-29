import requests
import json
import time

BASE_URL = "http://localhost:10001"

def push_context(scope, cid, payload):
    url = f"{BASE_URL}/v1/context"
    data = {
        "scope": scope,
        "context_id": cid,
        "version": 1,
        "payload": payload,
        "delivered_at": "2026-04-29T10:00:00Z"
    }
    resp = requests.post(url, json=data)
    print(f"Pushing {scope}/{cid}: {resp.status_code} - {resp.json()}")

def test_vera():
    # 1. Category Context
    dentist_cat = {
        "slug": "dentists",
        "offer_catalog": [
            {"title": "Dental Cleaning @ ₹299", "value": "299", "audience": "new_user"},
            {"title": "Free Consultation", "value": "0", "audience": "all"}
        ],
        "voice": {
            "tone": "peer_clinical",
            "vocab_allowed": ["fluoride varnish", "caries", "scaling"],
            "vocab_taboo": ["cure", "guaranteed"]
        },
        "peer_stats": {
            "avg_rating": 4.4,
            "avg_reviews": 62,
            "avg_ctr": 0.030,
            "scope": "South Delhi"
        },
        "digest": [
            {
                "id": "d_001",
                "kind": "research",
                "title": "3-mo fluoride recall cuts caries 38% better than 6-mo",
                "source": "JIDA Oct 2026, p.14",
                "summary": "Recent study shows high efficacy of 3-month recall."
            }
        ]
    }
    push_context("category", "dentists", dentist_cat)

    # 2. Merchant Context
    meera_merchant = {
        "merchant_id": "m_001",
        "category_slug": "dentists",
        "identity": {
            "name": "Dr. Meera's Dental Clinic",
            "city": "Delhi",
            "locality": "Lajpat Nagar",
            "verified": True,
            "languages": ["en", "hi"]
        },
        "subscription": {
            "status": "active",
            "plan": "Pro",
            "days_remaining": 82
        },
        "performance": {
            "window_days": 30,
            "views": 2410,
            "calls": 18,
            "directions": 45,
            "ctr": 0.021
        },
        "offers": [
            {"id": "o_001", "title": "Dental Cleaning @ ₹299", "status": "active"}
        ],
        "signals": ["ctr_below_peer_median"]
    }
    push_context("merchant", "m_001", meera_merchant)

    # 3. Trigger Context
    research_trigger = {
        "id": "trg_001",
        "scope": "merchant",
        "kind": "research_digest",
        "source": "external",
        "merchant_id": "m_001",
        "payload": {
            "category": "dentists",
            "top_item": "3-mo fluoride recall cuts caries 38% better"
        },
        "urgency": 2,
        "suppression_key": "research:dentists:2026-W17",
        "expires_at": "2026-05-03T00:00:00Z"
    }
    push_context("trigger", "trg_001", research_trigger)

    # 4. Tick
    print("\nTriggering tick...")
    tick_resp = requests.post(f"{BASE_URL}/v1/tick", json={"available_triggers": ["trg_001"]})
    print(f"Tick Response: {tick_resp.status_code}")
    print(json.dumps(tick_resp.json(), indent=2))

    if tick_resp.json().get("actions"):
        conv_id = tick_resp.json()["actions"][0]["conversation_id"]
        # 5. Reply
        print("\nTesting reply...")
        reply_resp = requests.post(f"{BASE_URL}/v1/reply", json={
            "conversation_id": conv_id,
            "merchant_id": "m_001",
            "message": "Yes, tell me more about the study."
        })
        print(f"Reply Response: {reply_resp.status_code}")
        print(json.dumps(reply_resp.json(), indent=2))

if __name__ == "__main__":
    test_vera()
