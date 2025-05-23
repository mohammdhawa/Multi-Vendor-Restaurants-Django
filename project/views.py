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
    }

    return render(request, 'home.html', context)

