import time
from fastapi import FastAPI, HTTPException, Request
from models import TickResponse, ReplyResponse, ComposedMessage
from storage import storage
from composer import composer
from typing import List, Dict, Any

app = FastAPI(title="Vera Merchant AI Assistant")

START_TIME = time.time()

@app.get("/")
async def root():
    return {
        "message": "Vera Merchant AI Assistant is Live!",
        "endpoints": {
            "health": "/v1/healthz",
            "metadata": "/v1/metadata",
            "docs": "/docs"
        }
    }

@app.get("/v1/healthz")
async def healthz():
    counts = {
        "category": len(storage.get_all_by_scope("category")),
        "merchant": len(storage.get_all_by_scope("merchant")),
        "customer": len(storage.get_all_by_scope("customer")),
        "trigger": len(storage.get_all_by_scope("trigger"))
    }
    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - START_TIME),
        "contexts_loaded": counts
    }

@app.get("/v1/metadata")
async def metadata():
    return {
        "team_name": "Vera Builders",
        "team_members": ["Assistant"],
        "model": "gemini-1.5-flash",
        "approach": "4-context framework with FastAPI and Google Generative AI",
        "version": "1.0.0"
    }

@app.post("/v1/context")
async def push_context(request: Request):
    body = await request.json()
    scope = body.get("scope")
    cid = body.get("context_id")
    version = body.get("version")
    payload = body.get("payload")

    if not all([scope, cid, version, payload]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    accepted, current_version = storage.store_context(scope, cid, version, payload)
    
    if not accepted:
        return {
            "accepted": False, 
            "reason": "stale_version", 
            "current_version": current_version
        }

    return {
        "accepted": True, 
        "ack_id": f"ack_{cid}_v{version}", 
        "stored_at": f"{time.time()}"
    }

@app.post("/v1/tick", response_model=TickResponse)
async def tick(request: Request):
    body = await request.json()
    available_triggers = body.get("available_triggers", [])
    
    actions = []
    for trg_id in available_triggers:
        trigger = storage.get_context("trigger", trg_id)
        if not trigger:
            continue
            
        merchant = storage.get_context("merchant", trigger.merchant_id)
        if not merchant:
            continue
            
        category = storage.get_context("category", merchant.category_slug)
        if not category:
            continue
            
        customer = None
        if trigger.customer_id:
            customer = storage.get_context("customer", trigger.customer_id)
            
        # Compose message
        composition = await composer.compose(category, merchant, trigger, customer)
        
        # Generate a unique conversation ID if starting new
        conv_id = f"conv_{trigger.merchant_id}_{int(time.time())}"
        
        action = ComposedMessage(
            conversation_id=conv_id,
            merchant_id=trigger.merchant_id,
            customer_id=trigger.customer_id,
            send_as=composition.get("send_as", "vera"),
            trigger_id=trg_id,
            body=composition.get("body", ""),
            cta=composition.get("cta", ""),
            suppression_key=trigger.suppression_key,
            rationale=composition.get("rationale", "")
        )
        
        # Log to conversation history
        storage.add_to_conversation(conv_id, {"from": "vera", "body": action.body})
        actions.append(action)
        
    return {"actions": actions}

@app.post("/v1/reply", response_model=ReplyResponse)
async def reply(request: Request):
    body = await request.json()
    conv_id = body.get("conversation_id")
    mid = body.get("merchant_id")
    msg = body.get("message")
    
    if not all([conv_id, mid, msg]):
        raise HTTPException(status_code=400, detail="Missing required fields")
        
    merchant = storage.get_context("merchant", mid)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
        
    category = storage.get_context("category", merchant.category_slug)
    
    # Store incoming message
    storage.add_to_conversation(conv_id, {"from": "merchant", "body": msg})
    
    # Generate response
    history = storage.get_conversation(conv_id)
    response = await composer.respond(history, merchant, category, msg)
    
    # If bot sends a reply, store it
    if response.get("action") == "send" and response.get("body"):
        storage.add_to_conversation(conv_id, {"from": "vera", "body": response["body"]})
        
    return response

# Standalone compose function for Challenge §7.1 compliance
def compose(category: dict, merchant: dict, trigger: dict, customer: dict | None = None) -> dict:
    """
    Standalone version for script-based evaluation.
    This runs synchronously as per the spec.
    """
    import asyncio
    from models import CategoryContext, MerchantContext, TriggerContext, CustomerContext
    
    # Convert dicts to models
    cat_model = CategoryContext(**category)
    mer_model = MerchantContext(**merchant)
    trg_model = TriggerContext(**trigger)
    cus_model = CustomerContext(**customer) if customer else None
    
    # Run the async composer synchronously
    return asyncio.run(composer.compose(cat_model, mer_model, trg_model, cus_model))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10001)
