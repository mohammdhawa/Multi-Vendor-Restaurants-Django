from django.shortcuts import render

from marketplace.models import Cart
from vendor.models import Vendor
from django.db.models import Q, Prefetch
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D # D = Distance
from django.contrib.gis.db.models.functions import Distance
from menue.models import Category


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

        # Process the response to convert food links
        processed_response = process_food_links(bot_response)

        return JsonResponse({
            'response': processed_response,
            'status': 'success'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"Chatbot API Error: {e}")
        return JsonResponse({'error': 'Something went wrong'}, status=500)


def process_food_links(response_text):
    """
    Convert [FOODLINK:id:name] format to clickable HTML links
    Place this in your main views.py file
    """
    import re

    # Pattern to match [FOODLINK:id:name]
    pattern = r'\[FOODLINK:(\d+):([^\]]+)\]'

    def replace_link(match):
        food_id = match.group(1)
        food_name = match.group(2)
        vendor = FoodItem.objects.get(id=food_id).vendor
        # Assuming your food detail URL pattern is 'food-detail/<int:id>/'
        # Adjust this URL pattern according to your actual URL structure
        return f'<a href="/marketplace/{vendor.slug}/" class="food-link" data-food-id="{vendor.slug}">{food_name}</a>'

    # Replace all food links in the response
    processed_text = re.sub(pattern, replace_link, response_text)

    return processed_text


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
        return "Üzgünüm, şu anda isteğinizi işleme koymada sorun yaşıyorum. Lütfen daha sonra tekrar deneyin."


def build_system_prompt(food_context, user):
    """
    Build system prompt for AI based on user's food history
    Place this in your main views.py file
    """
    base_prompt = """Sen çok restoranlı bir web sitesi için yardımcı bir yemek öneri asistanısın. 
        Görevin, kullanıcının diyet tercihleri ve kısıtlamalarına göre yiyecek öğeleri önermektir.

        ÖNEMLİ: Yiyecek öğeleri önerirken, bunları **tam olarak şu formatta** tıklanabilir bağlantılar olarak biçimlendirmelisin:
        [FOODLINK:food_id:food_name] — burada food_id gerçek kimlik, food_name ise görüntülenen isimdir.

        Örnek: "Keto diyeti için mükemmel olan [FOODLINK:15:Izgara Tavuk Salatası] öğesini öneriyorum."

        Kurallar:
        - Diyet tercihlerini sor (vejetaryen, vegan, keto, glutensiz vb.)
        - Belirli yiyecek öğelerinden bahsederken her zaman [FOODLINK:id:name] formatını kullan
        - Varsa, kullanıcının önceki siparişlerini dikkate al
        - Samimi ve sohbet havasında ol
        - Tercihleri daha iyi anlamak için her zaman takip soruları sor
        - Önerilen öğelerin kısa açıklamalarını sun
        - Bir yanıtta birden fazla öğe önerebilirsin
        """

    if user.is_authenticated:
        # Add user's previous orders context
        prev_items = food_context.get('prev_fooditems', [])
        if prev_items:
            prev_orders = ", ".join([f"{item['fooditem']} ({item['category']})" for item in prev_items[:5]])
            base_prompt += f"\n\nUser's recent orders: {prev_orders}"

        # Add available menu items with IDs
        all_items = food_context.get('all_fooditems', [])
        if all_items:
            menu_items = []
            for item in all_items[:20]:  # Limit to avoid token overflow
                menu_items.append(
                    f"ID:{item['id']} - {item['fooditem']} - {item['category']}: {item['description'][:50]}...")

            base_prompt += f"\n\nAvailable menu items (use the ID numbers in your recommendations):\n" + "\n".join(
                menu_items)
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


def food_detail(request, food_id):
    """
    Food detail view - create this if you don't have it already
    Place this in your main views.py file
    """
    try:
        food_item = FoodItem.objects.get(id=food_id)
        vendor = food_item.vendor
        categories = Category.objects.filter(vendor=vendor).prefetch_related(
                    Prefetch('category_food_item', queryset=FoodItem.objects.filter(is_available=True))
                )
        cart_items = Cart.objects.filter(user=request.user)
        context = {
            'vendor': vendor,
            'categories': categories,
            'cart_items': cart_items,
        }
        return render(request, 'marketplace/vendor_detail.html', context)
    except FoodItem.DoesNotExist:
        return render(request, '404.html', status=404)

# def vendor_detail(request, slug):
#     vendor = get_object_or_404(Vendor, slug=slug)
#     categories = Category.objects.filter(vendor=vendor).prefetch_related(
#         Prefetch('category_food_item', queryset=FoodItem.objects.filter(is_available=True))
#     )
#
#     if request.user.is_authenticated:
#         cart_items = Cart.objects.filter(user=request.user)
#         print('Cart items:')
#         print(cart_items)
#     else:
#         cart_items = None
#     context = {
#         'vendor': vendor,
#         'categories': categories,
#         'cart_items': cart_items,
#     }
#     return render(request, 'marketplace/vendor_detail.html', context)