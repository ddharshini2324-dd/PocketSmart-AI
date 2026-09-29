import os
import json
import urllib.parse
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

def extract_json(response_text: str) -> dict:
    cleaned = response_text.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)

def get_home_recommendations(data: dict) -> dict:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        Provide home interior suggestions in INR for India with total budget ₹{data['total_budget']}.
        Requirements: {data.get('num_lights', 0)} lights, {data.get('num_fans', 0)} fans, {data.get('num_furniture', 0)} furniture.
        Rooms: {', '.join(data.get('rooms', []))}.
        Special requests: {data.get('additional', 'None')}.

        Return ONLY valid JSON format:
        {{
          "total_budget": {data['total_budget']},
          "budget_breakdown": [
            {{
              "category": "Lighting",
              "allocation": 2000,
              "items": [
                {{
                  "name": "LED Warm Ceiling Light",
                  "description": "Energy efficient ambient light",
                  "estimated_price": 1500,
                  "quantity": 1,
                  "search_terms": "LED warm ceiling light"
                }}
              ]
            }}
          ]
        }}
        """
        res = model.generate_content(prompt)
        result = extract_json(res.text)

        for cat in result.get("budget_breakdown", []):
            for item in cat.get("items", []):
                st = urllib.parse.quote_plus(item.get("search_terms", ""))
                item["shopping_links"] = {
                    "Amazon": f"https://www.amazon.in/s?k={st}",
                    "Flipkart": f"https://www.flipkart.com/search?q={st}"
                }
        return result
    except Exception as e:
        st = urllib.parse.quote_plus("interior decor")
        return {
            "status": "success",
            "total_budget": data['total_budget'],
            "budget_breakdown": [
                {
                    "category": "Lighting & Electricals",
                    "allocation": data['total_budget'] * 0.3,
                    "items": [
                        {
                            "name": "Smart LED Lights & Fans",
                            "description": "Energy efficient ceiling lights and modern fans",
                            "estimated_price": data['total_budget'] * 0.3,
                            "quantity": data.get('num_lights', 1) + data.get('num_fans', 1),
                            "shopping_links": {
                                "Amazon": f"https://www.amazon.in/s?k={urllib.parse.quote_plus('smart ceiling lights')}",
                                "Flipkart": f"https://www.flipkart.com/search?q={urllib.parse.quote_plus('ceiling fan LED')}"
                            }
                        }
                    ]
                },
                {
                    "category": "Furniture & Decor",
                    "allocation": data['total_budget'] * 0.7,
                    "items": [
                        {
                            "name": "Modern Interior Furniture Set",
                            "description": "Ergonomic furniture matching room requirements",
                            "estimated_price": data['total_budget'] * 0.7,
                            "quantity": data.get('num_furniture', 1),
                            "shopping_links": {
                                "Amazon": f"https://www.amazon.in/s?k={urllib.parse.quote_plus('modern furniture')}",
                                "Flipkart": f"https://www.flipkart.com/search?q={urllib.parse.quote_plus('home decor furniture')}"
                            }
                        }
                    ]
                }
            ]
        }

def get_party_recommendations(data: dict) -> dict:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        Provide party planning recommendations in INR for India with total budget ₹{data['total_budget']}.
        Party Type: {data.get('party_type', 'Birthday')}.
        Guests: {data.get('num_guests', 10)}.
        Venue: {data.get('venue_type', 'Home')}.
        Catering needed: {data.get('needs_catering', True)}, Decoration needed: {data.get('needs_decoration', True)}, Entertainment: {data.get('needs_entertainment', True)}.

        Return ONLY valid JSON format:
        {{
          "total_budget": {data['total_budget']},
          "budget_breakdown": [
            {{
              "category": "Catering",
              "allocation": {data['total_budget'] * 0.4},
              "items": [
                {{
                  "name": "Party Food & Beverages",
                  "description": "Curated meal menu for guests",
                  "estimated_price": {data['total_budget'] * 0.4},
                  "quantity": {data.get('num_guests', 10)},
                  "search_terms": "party catering combo"
                }}
              ]
            }},
            {{
              "category": "Decoration",
              "allocation": {data['total_budget'] * 0.3},
              "items": [
                {{
                  "name": "Theme Balloon & Banner Kit",
                  "description": "Party theme backdrop and lights",
                  "estimated_price": {data['total_budget'] * 0.3},
                  "quantity": 1,
                  "search_terms": "party decoration items"
                }}
              ]
            }}
          ]
        }}
        """
        res = model.generate_content(prompt)
        result = extract_json(res.text)

        for cat in result.get("budget_breakdown", []):
            for item in cat.get("items", []):
                st = urllib.parse.quote_plus(item.get("search_terms", ""))
                item["shopping_links"] = {
                    "Swiggy": f"https://www.swiggy.com/search?query={st}",
                    "Zomato": f"https://www.zomato.com/search?q={st}",
                    "Amazon": f"https://www.amazon.in/s?k={st}",
                    "Flipkart": f"https://www.flipkart.com/search?q={st}"
                }
        return result
    except Exception as e:
        st_cat = urllib.parse.quote_plus("party food")
        st_dec = urllib.parse.quote_plus("party decorations")
        return {
            "status": "success",
            "total_budget": data['total_budget'],
            "budget_breakdown": [
                {
                    "category": "Catering & Refreshments",
                    "allocation": data['total_budget'] * 0.5,
                    "items": [
                        {
                            "name": f"Party Food Setup for {data.get('num_guests', 10)} guests",
                            "description": "Delicious party meal & snacks pack",
                            "estimated_price": data['total_budget'] * 0.5,
                            "quantity": data.get('num_guests', 10),
                            "shopping_links": {
                                "Swiggy": f"https://www.swiggy.com/search?query={st_cat}",
                                "Zomato": f"https://www.zomato.com/search?q={st_cat}"
                            }
                        }
                    ]
                },
                {
                    "category": "Decorations & Venue",
                    "allocation": data['total_budget'] * 0.5,
                    "items": [
                        {
                            "name": f"{data.get('party_type', 'Event')} Decor Kit & Venue Accessories",
                            "description": "Balloons, banners, LED lights kit",
                            "estimated_price": data['total_budget'] * 0.5,
                            "quantity": 1,
                            "shopping_links": {
                                "Amazon": f"https://www.amazon.in/s?k={st_dec}",
                                "Flipkart": f"https://www.flipkart.com/search?q={st_dec}",
                                "OYO": f"https://www.oyorooms.com/search/?location={urllib.parse.quote_plus('party hall')}"
                            }
                        }
                    ]
                }
            ]
        }

def get_jewelry_recommendations(data: dict, image_path: str = None) -> dict:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        base_prompt = f"""
        Provide jewelry recommendations in INR for India with total budget ₹{data['total_budget']}.
        Occasion: {data.get('occasion', 'Wedding')}.
        Preferences: {data.get('preferences', 'Traditional')}.
        """
        
        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
            prompt = base_prompt + """
            Analyze the uploaded outfit image (colors, design, formality) and suggest matching jewelry.
            Return ONLY valid JSON format:
            {
              "outfit_analysis": {"colors": "blue & silver", "style": "ethnic", "formality": "festive"},
              "total_budget": """ + str(data['total_budget']) + """,
              "jewelry_recommendations": [
                {
                  "item_type": "Necklace Set",
                  "description": "Matching necklace with earrings",
                  "estimated_price": """ + str(data['total_budget'] * 0.6) + """,
                  "search_terms": "designer necklace set"
                }
              ]
            }
            """
            res = model.generate_content([prompt, img])
        else:
            prompt = base_prompt + """
            Return ONLY valid JSON format:
            {
              "total_budget": """ + str(data['total_budget']) + """,
              "jewelry_recommendations": [
                {
                  "item_type": "Necklace Set",
                  "description": "Elegant jewelry pieces matching occasion",
                  "estimated_price": """ + str(data['total_budget'] * 0.6) + """,
                  "search_terms": "traditional jewelry set"
                }
              ]
            }
            """
            res = model.generate_content(prompt)

        result = extract_json(res.text)
        for item in result.get("jewelry_recommendations", []):
            st = urllib.parse.quote_plus(item.get("search_terms", ""))
            item["shopping_links"] = {
                "Amazon": f"https://www.amazon.in/s?k={st}",
                "Flipkart": f"https://www.flipkart.com/search?q={st}",
                "Caratlane": f"https://www.caratlane.com/search?q={st}",
                "Tanishq": f"https://www.tanishq.co.in/search?q={st}"
            }
        return result
    except Exception as e:
        st_j = urllib.parse.quote_plus("designer jewelry")
        return {
            "status": "success",
            "total_budget": data['total_budget'],
            "jewelry_recommendations": [
                {
                    "item_type": f"Jewelry Collection for {data.get('occasion', 'Special Event')}",
                    "description": "Curated matching necklace, bangles, and earrings set",
                    "estimated_price": data['total_budget'],
                    "shopping_links": {
                        "Amazon": f"https://www.amazon.in/s?k={st_j}",
                        "Flipkart": f"https://www.flipkart.com/search?q={st_j}",
                        "Caratlane": f"https://www.caratlane.com/search?q={st_j}",
                        "Tanishq": f"https://www.tanishq.co.in/search?q={st_j}"
                    }
                }
            ]
        }