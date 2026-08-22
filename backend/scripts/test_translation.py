import asyncio
from app.services.translation.indictrans2_provider import IndicTrans2Provider

async def main():
    provider = IndicTrans2Provider()
    print("Testing Hindi translation...")
    hi = await provider.translate_text("PM Kisan Samman Nidhi", "en", "hi")
    print(f"Hindi: {hi}")
    
    print("Testing Tamil translation...")
    ta = await provider.translate_text("PM Kisan Samman Nidhi", "en", "ta")
    print(f"Tamil: {ta}")

if __name__ == "__main__":
    asyncio.run(main())
