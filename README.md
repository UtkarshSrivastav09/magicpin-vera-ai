# Vera Merchant AI Assistant — magicpin AI Challenge

This is my submission for the magicpin AI Challenge. Vera is a state-of-the-art AI assistant designed to engage merchants on WhatsApp using a sophisticated 4-context framework.

## Approach & Design Decisions

### 1. The 4-Context Engine
Vera doesn't just send generic nudges. Every message is composed by analyzing:
- **Category Knowledge**: Vertical-specific rules, vocabulary, and peer benchmarks.
- **Merchant State**: Real-time performance deltas, active offers, and history.
- **Dynamic Triggers**: External events (news, festivals) and internal signals (perf spikes).
- **Customer Lifecycle**: For on-behalf-of messaging, honoring patient history and preferences.

### 2. High-Performance Stack
- **FastAPI**: Used for asynchronous processing and strict schema validation.
- **Pydantic**: Ensures data integrity across all 4 context layers.
- **Gemini 1.5 Flash**: Leveraged for high-speed, high-quality Hinglish composition.

### 3. Voice & Tone
Vera adopts a "Peer/Colleague" persona. For dentists, she uses clinical terminology and source citations. For restaurants, she speaks the language of local business growth.

## Tradeoffs & Constraints
- **In-Memory Storage**: For the purpose of this challenge, contexts are stored in memory. For production, a persistent Redis/PostgreSQL layer would be added.
- **Hinglish Balance**: The model is prompted to use Hinglish code-mixing only when the merchant's preference indicates it, ensuring clarity for all audiences.

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file with your API key:
   ```env
   GOOGLE_API_KEY=your_key_here
   ```
3. Run the server:
   ```bash
   python main.py
   ```
4. Run the verification script:
   ```bash
   python test_vera.py
   ```
