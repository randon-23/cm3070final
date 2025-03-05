from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from django.db.models import F, Q, Value
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from accounts_notifs.models import Account
from geopy.distance import geodesic
from .models import VolunteerOpportunity
from .serializers import VolunteerOpportunitySerializer
import json

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_opportunities(request):
    if request.method == "GET":
        account = request.user
        if not account.is_volunteer():
            return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            query_params = {key: request.GET.getlist(key) for key in request.GET.keys()}

            work_basis = query_params.get("work_basis", [""])[0]
            duration = query_params.get("duration", [""])[0]
            one_time = "on" in query_params.get("one_time", []) # Converts to boolean
            ongoing = "on" in query_params.get("ongoing", []) # Converts to boolean
            area_of_work = query_params.get("area_of_work", []) # List of strings
            days_of_week = query_params.get("days_of_week", []) # List of strings
            requirements = query_params.get("requirements", []) # List of strings
            languages = query_params.get("languages", []) # List of strings
            start_date = query_params.get("start_date", [""])[0]
            end_date = query_params.get("end_date", [""])[0]
            
            location_input = query_params.get("location_input", [""])[0]
            proximity = query_params.get("proximity", [""])[0]
            location = query_params.get("location", [""])[0]

            opportunities = VolunteerOpportunity.objects.filter(status="upcoming")

            # Filter by Work Type
            if work_basis and work_basis != "both":
                opportunities = opportunities.filter(work_basis=work_basis)

            # Filter by Duration
            if duration:
                opportunities = opportunities.filter(duration=duration)

            # Filter by Opportunity Type
            if one_time and not ongoing:
                opportunities = opportunities.filter(ongoing=False)
            elif ongoing and not one_time:
                opportunities = opportunities.filter(ongoing=True)

            # Filter by Fields of Interest
            if area_of_work:
                opportunities = opportunities.filter(area_of_work__in=area_of_work)

            # Filter by Days of the Week
            if days_of_week:
                opportunities = opportunities.filter(days_of_week__contains=days_of_week)

            # Filter by Skills/Requirements
            if requirements:
                opportunities = opportunities.filter(requirements__contains=requirements)

            # Filter by Languages
            if languages:
                opportunities = opportunities.filter(languages__contains=languages)

            # Filter by Date Range
            if start_date:
                opportunities = opportunities.filter(opportunity_date__gte=start_date)
            if end_date:
                opportunities = opportunities.filter(opportunity_date__lte=end_date)

            # Filter by Location (if enabled)
            if location_input and proximity:
                try:
                    location_data = json.loads(location)
                    user_lat, user_lon = location_data["lat"], location_data["lon"]
                    
                    def is_within_distance(opportunity):
                        if "lat" in opportunity.required_location and "lon" in opportunity.required_location:
                            opp_lat = opportunity.required_location["lat"]
                            opp_lon = opportunity.required_location["lon"]
                            distance = geodesic((user_lat, user_lon), (opp_lat, opp_lon)).km
                            print(f"Checking opportunity: {opportunity.title} → Distance: {distance} km")
                            return distance <= float(proximity[0])
                        return False

                    opportunities = [opp for opp in opportunities if is_within_distance(opp)]

                except json.JSONDecodeError:
                    print("Invalid location data, skipping location filtering.")

            # Serialize and return results
            serializer = VolunteerOpportunitySerializer(opportunities, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nearby_opportunities(request):
    
    return Response(status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_latest_opportunities(request):
    if request.method == "GET":
        if not request.user.is_volunteer():
            return Response(status=status.HTTP_403_FORBIDDEN)
        latest_opportunities = VolunteerOpportunity.objects.filter(status="upcoming").order_by("-created_at")[:5]
        serializer = VolunteerOpportunitySerializer(latest_opportunities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_opportunities(request):
    return Response(status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_organization_opportunities(request):
    return Response(status=status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_opportunity(request):
    return Response(status=status.HTTP_200_OK)