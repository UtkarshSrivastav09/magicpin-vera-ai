import os
import json
import google.generativeai as genai
from typing import Optional, List, Dict
from models import CategoryContext, MerchantContext, TriggerContext, CustomerContext
from dotenv import load_dotenv

load_dotenv()

class VeraComposer:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or "YOUR_ACTUAL_API_KEY" in api_key:
            print("WARNING: No valid GOOGLE_API_KEY found. Vera is running in 'Smart Template' fallback mode.")
            self.use_mock = True
        else:
            print(f"Vera AI Initialized with key: {api_key[:4]}...{api_key[-4:]}")
            self.use_mock = False
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                print(f"ERROR: Failed to configure Gemini: {e}")
                self.use_mock = True

    async def compose(self, 
                      category: CategoryContext, 
                      merchant: MerchantContext, 
                      trigger: TriggerContext, 
                      customer: Optional[CustomerContext] = None) -> Dict:
        
        if self.use_mock:
            return self._smart_template_compose(category, merchant, trigger, customer)

        prompt = self._build_compose_prompt(category, merchant, trigger, customer)
        
        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            print(f"LLM Composition error: {e}")
            return self._smart_template_compose(category, merchant, trigger, customer)

    def _build_compose_prompt(self, 
                            category: CategoryContext, 
                            merchant: MerchantContext, 
                            trigger: TriggerContext, 
                            customer: Optional[CustomerContext] = None) -> str:
        
        context_str = f"""
        CATEGORY CONTEXT:
        Vertical: {category.slug}
        Tone/Voice: {category.voice.tone}
        Allowed Vocabulary: {category.voice.vocab_allowed}
        Taboos: {category.voice.vocab_taboo}
        Offer Catalog: {[o.title for o in category.offer_catalog]}
        Peer Stats: {category.peer_stats.dict()}
        Recent Digest Items: {[d.title for d in category.digest[:3]]}

        MERCHANT CONTEXT:
        Name: {merchant.identity.name}
        Locality: {merchant.identity.locality}, {merchant.identity.city}
        Languages: {merchant.identity.languages}
        Performance (30d): {merchant.performance.dict()}
        Active Offers: {[o.title for o in merchant.offers if o.status == 'active']}
        Signals: {merchant.signals}

        TRIGGER CONTEXT:
        Kind: {trigger.kind}
        Payload: {trigger.payload}
        Urgency: {trigger.urgency}
        """

        if customer:
            context_str += f"""
            CUSTOMER CONTEXT (ON-BEHALF-OF MESSAGE):
            Name: {customer.identity.name}
            State: {customer.state}
            Relationship: {customer.relationship.dict()}
            Preferences: {customer.preferences}
            Language Pref: {customer.identity.language_pref}
            """

        instruction = """
        TASK: Compose a WhatsApp message for this merchant or customer.
        RULES:
        1. Keep length ≤ 320 chars (aim 150-200).
        2. NO URLs.
        3. Single primary CTA (Call to Action).
        4. Specificity wins: Anchor on a verifiable fact (number, date, headline).
        5. Voice Match: Use a peer/colleague tone (clinical for dentists, operator-to-operator for restaurants).
        6. Hinglish: If merchant/customer language preference includes Hindi, use a natural Hindi-English code-mix.
        7. No fabrications: If data isn't in context, don't invent it.

        RESPOND ONLY IN JSON:
        {
            "body": "The message text",
            "cta": "binary (YES/STOP) or open_ended",
            "send_as": "vera" or "merchant_on_behalf",
            "suppression_key": "from trigger",
            "rationale": "Short explanation of why this message"
        }
        """

        return context_str + instruction

    def _smart_template_compose(self, 
                               category: CategoryContext, 
                               merchant: MerchantContext, 
                               trigger: TriggerContext, 
                               customer: Optional[CustomerContext] = None) -> Dict:
        """A high-quality fallback that uses real data context to build a specific message."""
        
        if trigger.kind == "research_digest":
            top_item = trigger.payload.get("top_item", "latest research")
            name = merchant.identity.name
            salutation = f"Dr. {name.replace('Dr. ', '')}" if "dentist" in category.slug else name
            body = f"{salutation}, JIDA's Oct issue landed. One item relevant to your patients — {top_item}. Worth a look? Want me to pull the abstract for you?"
            rationale = "Smart template fallback: clinical anchor."
        elif trigger.kind == "perf_spike":
            views = merchant.performance.views
            body = f"Hi {merchant.identity.name}, great news! Your profile views spiked to {views} this week. Want to see what's driving the traffic?"
            rationale = "Smart template for performance spike."
        else:
            body = f"Hi {merchant.identity.name}, I noticed a {trigger.kind} event for {merchant.identity.locality}. Want to see how we can use this to grow your business?"
            rationale = "Smart template fallback: contextual nudge."

        return {
            "body": body,
            "cta": "open_ended",
            "send_as": "vera",
            "suppression_key": trigger.suppression_key,
            "rationale": rationale
        }

    async def respond(self, 
                      conversation_history: List[Dict], 
                      merchant: MerchantContext, 
                      category: CategoryContext,
                      latest_message: str) -> Dict:
        
        if self.use_mock:
            return {
                "action": "send", 
                "body": f"Understood! Let's move forward with that. I'll prepare the details for {merchant.identity.name} now.",
                "cta": "open_ended",
                "rationale": "Smart response fallback."
            }

        prompt = self._build_compose_prompt_respond(conversation_history, merchant, category, latest_message)
        
        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            print(f"LLM Response error: {e}")
            return {"action": "end", "rationale": "Error in response generation"}

    def _build_compose_prompt_respond(self, history, merchant, category, latest_message):
        return f"""
        CONVERSATION HISTORY: {history}
        LATEST MESSAGE: "{latest_message}"
        MERCHANT: {merchant.identity.name}
        CATEGORY: {category.slug}
        
        TASK: Decide how to respond. 
        - Auto-reply -> end.
        - Interest -> send.
        - Hostile -> end.
        
        RESPOND IN JSON: {{"action": "send/wait/end", "body": "...", "cta": "...", "rationale": "..."}}
        """

composer = VeraComposer()
