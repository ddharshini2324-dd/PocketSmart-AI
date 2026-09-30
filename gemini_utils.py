import os
import json
import re
import urllib.parse
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

def extract_json_from_response(text: str) -> dict:
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(text)
    except Exception:
        return {}

def get_home_recommendations(data: dict) -> dict:
    total_budget = float(data.get("total_budget", 50000))
    num_lights = int(data.get("num_lights", 2))
    num_fans = int(data.get("num_fans", 1))
    num_furniture = int(data.get("num_furniture", 1))
    num_dining = int(data.get("num_dining_tables", 0))
    
    prompt = f"""
    I need interior design product recommendations for a home in India with a total budget of ₹{total_budget:.2f}.
    Requirements:
    - {num_lights} lights/lighting fixtures
    - {num_fans} ceiling fans
    - {num_furniture} furniture pieces
    - {num_dining} dining tables
    
    Format your response as strict JSON:
    {{
      "total_budget": {total_budget},
      "budget_breakdown": [
        {{
          "category": "Lighting & Electricals",
          "allocation": {total_budget * 0.3},
          "items": [
            {{
              "name": "Smart LED Ceiling Light Set",
              "description": "Energy efficient ambient lighting for living rooms.",
              "estimated_price": {total_budget * 0.15},
              "quantity": {num_lights},
              "search_terms": "Smart LED Ceiling Lights"
            }}
          ]
        }},
        {{
          "category": "Furniture & Decor",
          "allocation": {total_budget * 0.7},
          "items": [
            {{
              "name": "Modern Wooden Sofa Set",
              "description": "Compact ergonomic sofa set suitable for modern Indian apartments.",
              "estimated_price": {total_budget * 0.5},
              "quantity": {num_furniture},
              "search_terms": "Modern Wooden Sofa Set"
            }}
          ]
        }}
      ],
      "additional_suggestions": ["Explore festival discounts on e-commerce platforms."]
    }}
    Ensure all prices are in INR and total cost does not exceed ₹{total_budget}.
    """
    try:
        response = model.generate_content(prompt)
        res = extract_json_from_response(response.text)
        if not res or "budget_breakdown" not in res:
            raise ValueError("Invalid JSON returned")
    except Exception:
        res = {
            "total_budget": total_budget,
            "budget_breakdown": [
                {
                    "category": "Lighting & Electricals",
                    "allocation": total_budget * 0.3,
                    "items": [{
                        "name": "Modular LED Lighting",
                        "description": "Energy efficient lighting setup.",
                        "estimated_price": total_budget * 0.2,
                        "quantity": num_lights,
                        "search_terms": "Modular LED Lights"
                    }]
                },
                {
                    "category": "Furniture",
                    "allocation": total_budget * 0.7,
                    "items": [{
                        "name": "Comfort Furniture Set",
                        "description": "Standard room furniture setup.",
                        "estimated_price": total_budget * 0.5,
                        "quantity": num_furniture,
                        "search_terms": "Modern Furniture Set"
                    }]
                }
            ],
            "additional_suggestions": ["Compare prices on IKEA and Amazon before buying."]
        }
        
    for category in res.get("budget_breakdown", []):
        for item in category.get("items", []):
            st = item.get("search_terms") or item.get("name", "")
            q_st = urllib.parse.quote_plus(st)
            item["shopping_links"] = {
                "Amazon": f"https://www.amazon.in/s?k={q_st}",
                "Flipkart": f"https://www.flipkart.com/search?q={q_st}",
                "IKEA": f"https://www.ikea.com/in/en/search/?q={q_st}",
                "Myntra": f"https://www.myntra.com/{q_st}",
                "Ajio": f"https://www.ajio.com/search/?text={q_st}"
            }
    return res

def get_party_recommendations(data: dict) -> dict:
    total_budget = float(data.get("total_budget", 15000))
    party_type = data.get("party_type", "Birthday Party")
    num_guests = int(data.get("num_guests", 20))
    venue_type = data.get("venue_type", "Home")
    
    prompt = f"""
    I need party planning recommendations for India with a total budget of ₹{total_budget:.2f}.
    Party Details: Type: {party_type}, Guests: {num_guests}, Venue: {venue_type}.
    
    Format output as strict JSON:
    {{
      "total_budget": {total_budget},
      "budget_breakdown": [
        {{
          "category": "Catering",
          "allocation": {total_budget * 0.6},
          "items": [
            {{
              "name": "Party Buffet Combo",
              "description": "Catering package for {num_guests} guests.",
              "estimated_price": {total_budget * 0.55},
              "quantity": 1,
              "search_terms": "Party Catering Service"
            }}
          ]
        }},
        {{
          "category": "Decoration",
          "allocation": {total_budget * 0.3},
          "items": [
            {{
              "name": "Theme Decoration Kit",
              "description": "Balloons, banners, and backdrop set.",
              "estimated_price": {total_budget * 0.25},
              "quantity": 1,
              "search_terms": "Party Decoration Kit"
            }}
          ]
        }}
      ],
      "additional_suggestions": ["Use digital invites to cut unnecessary costs."]
    }}
    """
    try:
        response = model.generate_content(prompt)
        res = extract_json_from_response(response.text)
        if not res or "budget_breakdown" not in res:
            raise ValueError("Invalid JSON returned")
    except Exception:
        res = {
            "total_budget": total_budget,
            "budget_breakdown": [
                {
                    "category": "Catering",
                    "allocation": total_budget * 0.6,
                    "items": [{
                        "name": "Event Food Catering",
                        "description": f"Standard meals for {num_guests} guests.",
                        "estimated_price": total_budget * 0.5,
                        "quantity": 1,
                        "search_terms": "Party Food Delivery"
                    }]
                },
                {
                    "category": "Decoration",
                    "allocation": total_budget * 0.3,
                    "items": [{
                        "name": "Party Prop Pack",
                        "description": "Decorations suitable for event setup.",
                        "estimated_price": total_budget * 0.25,
                        "quantity": 1,
                        "search_terms": "Theme Party Supplies"
                    }]
                }
            ],
            "additional_suggestions": ["Opt for potluck meals or home catering options."]
        }

    category_platforms = {
        "catering": ["swiggy", "zomato", "amazon"],
        "food": ["swiggy", "zomato"],
        "venue": ["google", "booking", "makemytrip", "oyorooms", "nobroker"],
        "decoration": ["amazon", "flipkart", "meesho"],
        "entertainment": ["bookmyshow", "amazon"]
    }
    
    for category in res.get("budget_breakdown", []):
        cat_name = category.get("category", "").lower()
        platforms = category_platforms.get(cat_name, ["amazon", "flipkart", "google"])
        for item in category.get("items", []):
            st = item.get("search_terms") or item.get("name", "")
            q_st = urllib.parse.quote_plus(st)
            links = {}
            if "amazon" in platforms: links["Amazon"] = f"https://www.amazon.in/s?k={q_st}"
            if "flipkart" in platforms: links["Flipkart"] = f"https://www.flipkart.com/search?q={q_st}"
            if "swiggy" in platforms: links["Swiggy"] = f"https://www.swiggy.com/search?query={q_st}"
            if "zomato" in platforms: links["Zomato"] = f"https://www.zomato.com/search?q={q_st}"
            if "bookmyshow" in platforms: links["BookMyShow"] = f"https://in.bookmyshow.com/search?q={q_st}"
            if "oyorooms" in platforms: links["OYO"] = f"https://www.oyorooms.com/search/?location={q_st}"
            if "google" in platforms: links["Google"] = f"https://www.google.com/search?q={q_st}"
            item["shopping_links"] = links
    return res

def get_jewelry_recommendations(data: dict, image_path: str = None) -> dict:
    total_budget = float(data.get("total_budget", 20000))
    occasion = data.get("occasion", "Wedding")
    preferences = data.get("preferences", "Gold Finish")
    
    prompt = f"""
    Provide Indian market jewelry recommendations for Budget ₹{total_budget:.2f}, Occasion: {occasion}, Style: {preferences}.
    Format output as strict JSON:
    {{
      "total_budget": {total_budget},
      "jewelry_recommendations": [
        {{
          "item_type": "Ethnic Necklace Set",
          "description": "Gold-plated choker necklace with matching earrings.",
          "style": "Traditional",
          "estimated_price": {total_budget * 0.6},
          "search_terms": "Gold Plated Necklace Set"
        }},
        {{
          "item_type": "Designer Bangles Set",
          "description": "Matching bangle pair for festive attire.",
          "style": "Ethnic",
          "estimated_price": {total_budget * 0.3},
          "search_terms": "Ethnic Bangle Set"
        }}
      ],
      "styling_tips": ["Match metal undertones with your outfit's embroidery."]
    }}
    """
    try:
        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
            response = model.generate_content([prompt, img])
        else:
            response = model.generate_content(prompt)
            
        res = extract_json_from_response(response.text)
        if not res or "jewelry_recommendations" not in res:
            raise ValueError("Invalid JSON returned")
    except Exception:
        res = {
            "total_budget": total_budget,
            "jewelry_recommendations": [
                {
                    "item_type": "Gold Finish Necklace",
                    "description": "Elegant necklace matching traditional Indian outfits.",
                    "style": "Classic",
                    "estimated_price": total_budget * 0.6,
                    "search_terms": "Gold Finish Choker Set"
                },
                {
                    "item_type": "Matching Earrings",
                    "description": "Lightweight statement earrings.",
                    "style": "Traditional",
                    "estimated_price": total_budget * 0.25,
                    "search_terms": "Statement Ethnic Earrings"
                }
            ],
            "styling_tips": ["Keep accessories subtle if the dress features heavy embroidery."]
        }
        
    for item in res.get("jewelry_recommendations", []):
        st = item.get("search_terms") or item.get("item_type", "")
        q_st = urllib.parse.quote_plus(st)
        item["shopping_links"] = {
            "Amazon": f"https://www.amazon.in/s?k={q_st}",
            "Flipkart": f"https://www.flipkart.com/search?q={q_st}",
            "Tanishq": f"https://www.tanishq.co.in/search?q={q_st}",
            "BlueStone": f"https://www.bluestone.com/search.html?query={q_st}",
            "CaratLane": f"https://www.caratlane.com/search?q={q_st}",
            "Meesho": f"https://www.meesho.com/search?q={q_st}"
        }
    return res