import redis
import json
from google.adk.agents import Agent
from fastapi.responses import StreamingResponse


r = redis.Redis(host='localhost', port=6379, db=0)

def add_item(user_id: str, item_name: str, details: str = ""):
        """Adds an item to the user's specific Redis list."""
        item_data = {"name": item_name, "details": details}
        # Store as a JSON string in a Redis List
        key = f"user:{user_id}:items"
        r.expire(key, 3600)
        r.lpush(key, json.dumps(item_data))
        return f"Added {item_name} to your session storage."

def list_items(user_id: str):
        """Retrieves all items for a specific user."""
        print(f"Listing items for user_id: {user_id}")
        items = r.lrange(f"user:{user_id}:items", 0, -1)
        return [json.loads(i) for i in items]

def remove_item(user_id: str, item_name: str):
        """Removes an item by name from the user's storage."""
        items = r.lrange(f"user:{user_id}:items", 0, -1)
        for item_str in items:
            if json.loads(item_str)['name'] == item_name:
                r.lrem(f"user:{user_id}:items", 1, item_str)
                return f"Removed {item_name}."
        return "Item not found."




