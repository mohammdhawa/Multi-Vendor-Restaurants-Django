from django.shortcuts import render
from vendor.models import Vendor
from django.db.models import Q
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D # D = Distance
from django.contrib.gis.db.models.functions import Distance


def get_or_set_current_location(request):
    if 'lat' in request.session and 'lng' in request.session:
        try:
            lat = request.session['lat']
            lng = request.session['lng']
            return lng, lat
        except (TypeError, ValueError):
            return None
    elif 'lat' in request.GET and 'lng' in request.GET:
        try:
            lat = request.GET.get('lat')
            lng = request.GET.get('lng')

            request.session['lat'] = lat
            request.session['lng'] = lng
            return lng, lat
        except (TypeError, ValueError):
            return None
    else:
        return None



def home(request):
    location = get_or_set_current_location(request)
    # Get food data for chatbot context
    food_context = food_data(request) if request.user.is_authenticated else {'prev_fooditems': [], 'all_fooditems': []}

    if location is not None:
        try:
            lng, lat = request.GET.get('lng'), request.GET.get('lat')
            # Ensure they are floats
            lng = float(lng)
            lat = float(lat)

            # Correct WKT format: POINT(longitude latitude)
            pnt = GEOSGeometry(f'POINT({float(lng)} {float(lat)})', srid=4326)
            print('pnt ==> ', pnt)

            # Query vendors within 200 km
            vendors = Vendor.objects.filter(
                user_profile__location__distance_lte=(pnt, D(km=2000))
            ).annotate(
                distance=Distance('user_profile__location', pnt)
            ).order_by('distance')

            for v in vendors:
                v.kms = round(v.distance.km, 1)
        except (ValueError, TypeError) as e:
            print("Error processing coordinates:", e)
            vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)[:8]
    else:
        vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)

    context = {
        'vendors': vendors,
        'food_context': food_context,
        'user_authenticated': request.user.is_authenticated
    }

    return render(request, 'home.html', context)


import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from openai import OpenAI
from orders.models import Order, OrderFood, FoodItem


@csrf_exempt
def chatbot_api(request):
    """
    API endpoint for chatbot communication
    Place this in your main views.py file
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        # Get user's food history and preferences
        food_context = {}
        if request.user.is_authenticated:
            food_context = food_data(request)

        # Generate AI response
        bot_response = get_chatbot_response(user_message, food_context, request.user)

        return JsonResponse({
            'response': bot_response,
            'status': 'success'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"Chatbot API Error: {e}")
        return JsonResponse({'error': 'Something went wrong'}, status=500)


def get_chatbot_response(user_message, food_context, user):
    """
    Generate chatbot response using AI API
    Place this in your main views.py file
    """
    client = OpenAI(
        base_url="https://api.aimlapi.com/v1",
        api_key="d25245ec15514e1db161232d4af35d7e",
    )

    # Build context for AI
    system_prompt = build_system_prompt(food_context, user)

    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-prover-v2",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            top_p=0.7,
            frequency_penalty=1,
            max_tokens=512,
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error during OpenAI call: {e}")
        return "I'm sorry, I'm having trouble processing your request right now. Please try again later."


def build_system_prompt(food_context, user):
    """
    Build system prompt for AI based on user's food history
    Place this in your main views.py file
    """
    base_prompt = """You are a helpful food recommendation assistant for a multi-restaurant website. 
    Your job is to recommend food items based on user's dietary preferences and restrictions.

    Guidelines:
    - Ask about dietary preferences (vegetarian, vegan, keto, gluten-free, etc.)
    - Recommend specific food items from our available menu
    - Consider user's previous orders if available
    - Be friendly and conversational
    - Always ask follow-up questions to better understand preferences
    - Provide brief descriptions of recommended items
    """

    if user.is_authenticated:
        # Add user's previous orders context
        prev_items = food_context.get('prev_fooditems', [])
        if prev_items:
            prev_orders = ", ".join([f"{item['fooditem']} ({item['category']})" for item in prev_items[:5]])
            base_prompt += f"\n\nUser's recent orders: {prev_orders}"

        # Add available menu items
        all_items = food_context.get('all_fooditems', [])
        if all_items:
            menu_items = []
            for item in all_items[:20]:  # Limit to avoid token overflow
                menu_items.append(f"{item['fooditem']} - {item['category']}: {item['description'][:50]}...")

            base_prompt += f"\n\nAvailable menu items:\n" + "\n".join(menu_items)
    else:
        base_prompt += "\n\nUser is not logged in. Encourage them to sign up for personalized recommendations."

    return base_prompt


def food_data(request):
    """
    Your existing food_data function - keep as is
    """
    order_foods = OrderFood.objects.filter(
        user=request.user,
        order__is_ordered=True,
        order__status='Completed'
    )

    data = [
        {
            "fooditem": item.fooditem.food_title,
            "category": item.fooditem.category.category_name,
            "description": item.fooditem.description,
            "quantity": item.quantity
        }
        for item in order_foods
    ]

    all_fooditems = FoodItem.objects.all()

    data2 = [
        {
            "id": item.id,
            "fooditem": item.food_title,
            "category": item.category.category_name,
            "description": item.description,
        }
        for item in all_fooditems
    ]

    context = {
        'prev_fooditems': data,
        'all_fooditems': data2,
    }

    return context