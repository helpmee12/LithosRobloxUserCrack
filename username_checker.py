import asyncio
import aiohttp
import random
import json
from typing import List, Dict, Any

class UsernameChecker:
    def __init__(self, min_length: int, max_length: int, count: int, webhook_url: str) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.count = count
        self.webhook_url = webhook_url
        self.csrf_token: str = None
        self.session: aiohttp.ClientSession = None

    async def get_csrf_token(self) -> None:
        async with self.session.post('https://economy.roblox.com/', ssl=False) as response:
            self.csrf_token = response.headers.get('x-csrf-token')

    async def is_username_available(self, username: str) -> bool:
        headers = {'x-csrf-token': self.csrf_token}
        async with self.session.get(
            f"https://auth.roblox.com/v2/usernames/validate?request.username={username}&request.birthday=01%2F01%2F2000&request.context=Signup",
            headers=headers,
            timeout=10,
            ssl=False
        ) as response:
            if response.status == 200:
                result = await response.text()
                return "Username is valid" in result
            elif response.status == 403:
                print("CSRF token expired. Getting a new one...")
                await self.get_csrf_token()
            else:
                print(f"Unexpected response: {response.status}")
            return False

    async def send_to_webhook(self, message: str) -> None:
        data = {"content": message}
        try:
            async with self.session.post(self.webhook_url, json=data, headers={"Content-Type": "application/json"}) as response:
                if response.status != 204:
                    print(f"Failed to send message to webhook: {response.status}")
        except Exception as e:
            print(f"Webhook request exception: {e}")

    def generate_usernames(self, length: int, count: int) -> List[str]:
        usernames = []
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
        for _ in range(count):
            username = ''.join(random.choice(characters) for _ in range(length))
            usernames.append(username)
        return usernames

    async def check_usernames_for_length(self, length: int) -> List[str]:
        usernames = self.generate_usernames(length, self.count)
        available_usernames = []
        for username in usernames:
            if await self.is_username_available(username):
                available_usernames.append(username)
                print(f"Username '{username}' is available.")
                await self.send_to_webhook(f"Username '{username}' is available.")
            else:
                print(f"Username '{username}' is taken.")
            await asyncio.sleep(0.1)
        return available_usernames

    async def check_usernames(self) -> List[str]:
        all_available_usernames = []
        for length in range(self.min_length, self.max_length + 1):
            print(f"Checking usernames of length {length}...")
            available_usernames = await self.check_usernames_for_length(length)
            all_available_usernames.extend(available_usernames)
        return all_available_usernames

    async def main(self) -> List[str]:
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=None))
        try:
            await self.get_csrf_token()
            available_usernames = await self.check_usernames()
            print(f"Available usernames: {available_usernames}")
            return available_usernames
        finally:
            await self.session.close()

def main_menu():
    print("Lithos User Cracker")
    
    min_length = 3
    max_length = 6
    count = 100
    webhook_url = "https://your-webhook-url-here"

    while True:
        print("1. Start checking usernames")
        print("2. Set webhook URL")
        print("3. Set username length range")
        print("4. Exit")

        choice = input("Enter your choice: ")
        if choice == '1':
            checker = UsernameChecker(min_length, max_length, count, webhook_url)
            loop = asyncio.get_event_loop()
            available_usernames = loop.run_until_complete(checker.main())
            print(f"Available usernames: {available_usernames}")
        elif choice == '2':
            webhook_url = input("Enter new webhook URL: ")
        elif choice == '3':
            min_length = int(input("Enter minimum username length: "))
            max_length = int(input("Enter maximum username length: "))
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main_menu()
