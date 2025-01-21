import aiohttp
import asyncio
from datetime import datetime, timedelta
import sys
import json
from typing import List, Dict

# Constants
API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"
SUPPORTED_CURRENCIES = ["USD", "EUR"]
MAX_DAYS = 10

class CurrencyExchangeService:
    """
    Сервіс для отримання курсу валют від ПриватБанку.
    """
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.session.close()

    async def fetch_exchange_rate(self, date: str) -> Dict:
        """
        Отримує курси валют на конкретну дату.
        """
        url = API_URL.format(date=date)
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    raise Exception(f"Error fetching data: {response.status}")
        except Exception as e:
            print(f"Error occurred while fetching data for {date}: {e}")
            return {}

class CurrencyExchangeProcessor:
    """
    Обробник даних курсу валют.
    """
    def __init__(self, currencies: List[str]):
        self.currencies = currencies

    def process_exchange_rates(self, raw_data: Dict) -> Dict:
        """
        Обробляє дані від API для вибраних валют.
        """
        result = {}
        if "exchangeRate" in raw_data:
            for rate in raw_data["exchangeRate"]:
                currency = rate.get("currency")
                if currency in self.currencies:
                    result[currency] = {
                        "sale": rate.get("saleRate"),
                        "purchase": rate.get("purchaseRate")
                    }
        return result

class CurrencyExchangeCLI:
    """
    Основний CLI для виводу результатів.
    """
    def __init__(self, processor: CurrencyExchangeProcessor):
        self.processor = processor

    async def get_exchange_rates(self, days: int) -> List[Dict]:
        """
        Отримує курси валют за останні кілька днів.
        """
        results = []
        async with CurrencyExchangeService() as service:
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime("%d.%m.%Y")
                raw_data = await service.fetch_exchange_rate(date)
                processed_data = self.processor.process_exchange_rates(raw_data)
                results.append({date: processed_data})
        return results

    async def run(self, days: int):
        """
        Запускає основний CLI інтерфейс.
        """
        if days > MAX_DAYS:
            print(f"Cannot fetch data for more than {MAX_DAYS} days.")
            return

        exchange_rates = await self.get_exchange_rates(days)
        print(json.dumps(exchange_rates, indent=2, ensure_ascii=False))

# Main function
async def main():
    try:
        days = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        currencies = sys.argv[2:] if len(sys.argv) > 2 else SUPPORTED_CURRENCIES

        processor = CurrencyExchangeProcessor(currencies)
        cli = CurrencyExchangeCLI(processor)
        await cli.run(days)
    except ValueError:
        print("Usage: python main.py <days> [currencies...]")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
