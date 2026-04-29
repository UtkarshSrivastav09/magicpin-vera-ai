from typing import Dict, Tuple, Any, Optional
from models import CategoryContext, MerchantContext, TriggerContext, CustomerContext

class VeraStorage:
    def __init__(self):
        # (scope, context_id) -> {"version": int, "payload": Any}
        self.contexts: Dict[Tuple[str, str], Dict[str, Any]] = {}
        # conversation_id -> List[Dict]
        self.conversations: Dict[str, list] = {}

    def store_context(self, scope: str, context_id: str, version: int, payload: Dict[str, Any]) -> Tuple[bool, Optional[int]]:
        key = (scope, context_id)
        current = self.contexts.get(key)
        
        if current and current["version"] >= version:
            return False, current["version"]
        
        # Convert raw payload to Pydantic model for validation
        try:
            validated_payload = self._validate_payload(scope, payload)
            self.contexts[key] = {"version": version, "payload": validated_payload}
            return True, None
        except Exception as e:
            print(f"Validation error for {scope}/{context_id}: {e}")
            raise e

    def _validate_payload(self, scope: str, payload: Dict[str, Any]):
        if scope == "category":
            return CategoryContext(**payload)
        elif scope == "merchant":
            return MerchantContext(**payload)
        elif scope == "trigger":
            return TriggerContext(**payload)
        elif scope == "customer":
            return CustomerContext(**payload)
        else:
            raise ValueError(f"Unknown scope: {scope}")

    def get_context(self, scope: str, context_id: str):
        data = self.contexts.get((scope, context_id))
        return data["payload"] if data else None

    def get_all_by_scope(self, scope: str) -> Dict[str, Any]:
        return {cid: data["payload"] for (s, cid), data in self.contexts.items() if s == scope}

    def add_to_conversation(self, conversation_id: str, turn: Dict[str, Any]):
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        self.conversations[conversation_id].append(turn)

    def get_conversation(self, conversation_id: str):
        return self.conversations.get(conversation_id, [])

# Singleton instance
storage = VeraStorage()
