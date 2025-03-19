from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from volunteers_organizations.models import VolunteerMatchingPreferences, Organization, Volunteer
from geopy.distance import geodesic
from .models import VolunteerOpportunity, VolunteerOpportunityApplication, VolunteerEngagement, VolunteerOpportunitySession, VolunteerSessionEngagement, VolunteerEngagementLog
from .serializers import VolunteerOpportunitySerializer, VolunteerOpportunityApplicationSerializer, VolunteerEngagementSerializer, VolunteerOpportunitySessionSerializer, VolunteerSessionEngagementSerializer, VolunteerEngagementLogSerializer
import json
from django.utils import timezone

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_opportunity(request, opportunity_id):
    if request.method == "GET":
        try:
            opportunity = VolunteerOpportunity.objects.get(volunteer_opportunity_id=opportunity_id)
        except VolunteerOpportunity.DoesNotExist:
            return Response({"error": "Opportunity not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.is_organization():
            if opportunity.organization.account != request.user:
                return Response({"error": "You can only view your own opportunities."}, status=status.HTTP_403_FORBIDDEN)

        serializer = VolunteerOpportunitySerializer(opportunity)
        return Response(serializer.data, status=status.HTTP_200_OK)    
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

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
    if request.method == "GET":
        account = request.user
        if not account.is_volunteer():
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Fetch the volunteer's location from their preferences
        try:
            preferences = VolunteerMatchingPreferences.objects.get(volunteer=account.volunteer)
            user_location = preferences.location  # JSON object { "lat": xx.x, "lon": yy.y }
        except VolunteerMatchingPreferences.DoesNotExist:
            return Response({"message": "Location preferences not set."}, status=status.HTTP_400_BAD_REQUEST)

        if not user_location or "lat" not in user_location or "lon" not in user_location:
            return Response({"message": "Invalid location data."}, status=status.HTTP_400_BAD_REQUEST)

        user_lat, user_lon = user_location["lat"], user_location["lon"]

        # Fetch all upcoming opportunities
        opportunities = VolunteerOpportunity.objects.filter(status="upcoming")

        # Compute distances and sort
        def compute_distance(opportunity):
            if "lat" in opportunity.required_location and "lon" in opportunity.required_location:
                opp_lat, opp_lon = opportunity.required_location["lat"], opportunity.required_location["lon"]
                return geodesic((user_lat, user_lon), (opp_lat, opp_lon)).km
            return float('inf')

        sorted_opportunities = sorted(opportunities, key=compute_distance)[:5]

        serializer = VolunteerOpportunitySerializer(sorted_opportunities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

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
def create_opportunity(request):
    if request.method == "POST":
        account = request.user
        if not account.is_organization():
            return Response({"error": "Only organizations can create opportunities."}, status=status.HTTP_403_FORBIDDEN)
        try:
            organization = Organization.objects.get(account=account)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        data["organization"] = organization.pk

        # Validate and create the opportunity
        serializer = VolunteerOpportunitySerializer(data=data, context={"request": request})
        if serializer.is_valid():
            opportunity = serializer.save()
            return Response({"message": "Successfully created opportunity", "data": serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "An error occurred when creating the opportunity", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Gets an organizations opportunities for their profile page for anyone viewing their profile    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_upcoming_opportunities(request, account_uuid):
    if request.method == "GET":
        try:
            organization = Organization.objects.get(account__account_uuid=account_uuid)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found."}, status=status.HTTP_404_NOT_FOUND)

        opportunities = VolunteerOpportunity.objects.filter(organization=organization, status="upcoming")
        serializer = VolunteerOpportunitySerializer(opportunities, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Gets an organizations opportunities for their Opportunities page
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_organization_opportunities(request):
    if request.method == "GET":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can view their opportunities."}, status=status.HTTP_403_FORBIDDEN)

        try:
            organization = Organization.objects.get(account=request.user)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found."}, status=status.HTTP_404_NOT_FOUND)

        opportunities = VolunteerOpportunity.objects.filter(organization=organization)
        serializer = VolunteerOpportunitySerializer(opportunities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cancel_opportunity(request, volunteer_opportunity_id):
    if request.method == "PATCH":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can update opportunity status."}, status=status.HTTP_403_FORBIDDEN)

        try:
            opportunity = VolunteerOpportunity.objects.get(volunteer_opportunity_id=volunteer_opportunity_id)
        except VolunteerOpportunity.DoesNotExist:
            return Response({"error": "Opportunity not found."}, status=status.HTTP_404_NOT_FOUND)

        if opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized to update this opportunity."}, status=status.HTTP_403_FORBIDDEN)

        if opportunity.status != "upcoming":
            return Response({"error": "Only upcoming opportunities can be modified."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if opportunity is ongoing and has any upcoming sessions
        if opportunity.ongoing:
            if VolunteerOpportunitySession.objects.filter(opportunity=opportunity, status="upcoming").exists():
                return Response(
                    {"error": "Cannot cancel opportunity while there are upcoming sessions. Cancel sessions first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        opportunity.status = "cancelled"
        opportunity.save()
        
        return Response({"message": "Opportunity successfully marked as cancelled."}, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def complete_opportunity(request, volunteer_opportunity_id):
    if not request.user.is_organization():
        return Response({"error": "Only organizations can update opportunity status."}, status=status.HTTP_403_FORBIDDEN)

    try:
        opportunity = VolunteerOpportunity.objects.get(volunteer_opportunity_id=volunteer_opportunity_id)
    except VolunteerOpportunity.DoesNotExist:
        return Response({"error": "Opportunity not found."}, status=status.HTTP_404_NOT_FOUND)

    if opportunity.organization.account != request.user:
        return Response({"error": "Unauthorized to update this opportunity."}, status=status.HTTP_403_FORBIDDEN)

    if opportunity.status != "upcoming":
        return Response({"error": "Only upcoming opportunities can be modified."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if opportunity is ongoing and has any upcoming sessions
    if opportunity.ongoing:
        if VolunteerOpportunitySession.objects.filter(opportunity=opportunity, status="upcoming").exists():
            return Response(
                {"error": "Cannot complete opportunity while there are upcoming sessions. Complete or cancel sessions first."},
                status=status.HTTP_400_BAD_REQUEST
            )

    opportunity.status = "completed"
    opportunity.save()
    
    return Response({"message": "Opportunity successfully marked as completed."}, status=status.HTTP_200_OK)

# Allows a volunteer to apply for an opportunity.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_application(request, volunteer_opportunity_id):
    if request.method == "POST":
        account = request.user
        if not request.user.is_volunteer():
            return Response({"error": "Only volunteers can apply for opportunities."}, status=status.HTTP_403_FORBIDDEN)

        try:
            volunteer = Volunteer.objects.get(account=account)
            volunteer_opportunity = VolunteerOpportunity.objects.get(volunteer_opportunity_id=volunteer_opportunity_id)
        except:
            return Response({"error": "Invalid object ID"}, status=status.HTTP_404_NOT_FOUND)
        data = request.data.copy()
        data["volunteer_id"] = volunteer.pk  # Ensure correct volunteer is set
        data["volunteer_opportunity_id"] = volunteer_opportunity.pk  # Ensure correct opportunity is set

        serializer = VolunteerOpportunityApplicationSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Successfully applied for opportunity.", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"message": "Application submission failed.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
# Allows an organization to accept a volunteer's application.
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def accept_application(request, application_id):
    if request.method == "PATCH":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can accept applications."}, status=status.HTTP_403_FORBIDDEN)
        try:
            application = VolunteerOpportunityApplication.objects.get(volunteer_opportunity_application_id=application_id)
        except VolunteerOpportunityApplication.DoesNotExist:
            return Response({"error": "Application not found."}, status=status.HTTP_404_NOT_FOUND)
        # Ensure only the organization that owns the opportunity can approve
        if application.volunteer_opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized to update this application."}, status=status.HTTP_403_FORBIDDEN)

        if application.application_status != "pending":
            return Response({"error": "Only pending applications can be accepted."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VolunteerOpportunityApplicationSerializer(application, data={"application_status": "accepted"}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Application accepted.", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"message": "Failed to accept application.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Allows an organization to reject a volunteer's application.
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def reject_application(request, application_id):
    if request.method == "PATCH":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can reject applications."}, status=status.HTTP_403_FORBIDDEN)
        try:
            application = VolunteerOpportunityApplication.objects.get(volunteer_opportunity_application_id=application_id)
        except VolunteerOpportunityApplication.DoesNotExist:
            return Response({"error": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure only the organization that owns the opportunity can reject
        if application.volunteer_opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized to update this application."}, status=status.HTTP_403_FORBIDDEN)

        if application.application_status != "pending":
            return Response({"error": "Only pending applications can be rejected."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VolunteerOpportunityApplicationSerializer(application, data={"application_status": "rejected"}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Application rejected.", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"message": "Failed to reject application.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Allows volunteers to cancel their own application if it is still pending.
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cancel_application(request, application_id):
    if request.method == "PATCH":
        if not request.user.is_volunteer():
            return Response({"error": "Only volunteers can cancel applications."}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = VolunteerOpportunityApplication.objects.get(volunteer_opportunity_application_id=application_id)
        except VolunteerOpportunityApplication.DoesNotExist:
            return Response({"error": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure only the volunteer who applied can cancel
        if application.volunteer.account != request.user:
            return Response({"error": "Unauthorized to update this application."}, status=status.HTTP_403_FORBIDDEN)

        if application.application_status != "pending":
            return Response({"error": "Only pending applications can be canceled."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VolunteerOpportunityApplicationSerializer(application, data={"application_status": "cancelled"}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Application successfully canceled.", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"message": "Failed to cancel application.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Returns all applications submitted by a given volunteer.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_volunteer_applications(request, account_uuid):
    if request.method == "GET":
        try:
            volunteer = Volunteer.objects.get(account__account_uuid=account_uuid)
        except Volunteer.DoesNotExist:
            return Response({"error": "Volunteer not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user != volunteer.account:
            return Response({"error": "Unauthorized access."}, status=status.HTTP_403_FORBIDDEN)

        applications = VolunteerOpportunityApplication.objects.filter(volunteer=volunteer)
        serializer = VolunteerOpportunityApplicationSerializer(applications, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Returns all applications received by an organization's opportunities.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_organization_applications(request, account_uuid):
    if request.method == "GET":
        try:
            organization = Organization.objects.get(account__account_uuid=account_uuid)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user != organization.account:
            return Response({"error": "Unauthorized access."}, status=status.HTTP_403_FORBIDDEN)

        applications = VolunteerOpportunityApplication.objects.filter(volunteer_opportunity__organization=organization)
        serializer = VolunteerOpportunityApplicationSerializer(applications, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Triggered when an application is accepted.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_engagement(request, application_id):
    if request.method == "POST":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can create engagements."}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = VolunteerOpportunityApplication.objects.get(volunteer_opportunity_application_id=application_id)
        except VolunteerOpportunityApplication.DoesNotExist:
            return Response({"error": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure only accepted applications can have engagements
        if application.application_status != "accepted":
            return Response({"error": "Only accepted applications can have engagements."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if engagement already exists
        if VolunteerEngagement.objects.filter(volunteer_opportunity_application=application).exists():
            return Response({"error": "Engagement already exists for this application."}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare engagement data
        data = {
            "volunteer_opportunity_application_id": application.pk,
            "engagement_status": "ongoing"
        }

        serializer = VolunteerEngagementSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Engagement successfully created.", "data": serializer.data}, status=status.HTTP_201_CREATED)

        return Response({"message": "Failed to create engagement.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Volunteers can retrieve their engagements.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_engagements(request, account_uuid):
    if request.method == "GET":
        try:
            volunteer = Volunteer.objects.get(account__account_uuid=account_uuid)
        except Volunteer.DoesNotExist:
            return Response({"error": "Volunteer not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure only the authenticated volunteer can access their own engagements
        if request.user != volunteer.account:
            return Response({"error": "Unauthorized access."}, status=status.HTTP_403_FORBIDDEN)

        engagements = VolunteerEngagement.objects.filter(volunteer=volunteer)
        serializer = VolunteerEngagementSerializer(engagements, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Fetches all an opportunities' engagements - used primarily prior to completing an opportunity.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_opportunity_engagements(request, volunteer_opportunity_id):
    if request.method == "GET":
        try:
            opportunity = VolunteerOpportunity.objects.get(volunteer_opportunity_id=volunteer_opportunity_id)
        except VolunteerOpportunity.DoesNotExist:
            return Response({"error": "Opportunity not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized access to get this opportunities' engagements."}, status=status.HTTP_403_FORBIDDEN)
        
        engagements = VolunteerEngagement.objects.filter(volunteer_opportunity_application__volunteer_opportunity=opportunity)
        serializer = VolunteerEngagementSerializer(engagements, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
# Triggered when an organization marks all engagements for an opportunity as completed.
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def complete_engagements_organization(request, volunteer_opportunity_id):
    if request.method == "PATCH":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can complete engagements."}, status=status.HTTP_403_FORBIDDEN)

        try:
            opportunity = VolunteerOpportunity.objects.get(volunteer_opportunity_id=volunteer_opportunity_id)
        except VolunteerOpportunity.DoesNotExist:
            return Response({"error": "Opportunity not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure only the correct organization is updating
        if opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized to update engagements for this opportunity."}, status=status.HTTP_403_FORBIDDEN)

        engagements = VolunteerEngagement.objects.filter(volunteer_opportunity_application__volunteer_opportunity=opportunity, engagement_status="ongoing")

        if not engagements.exists():
            return Response({"error": "No engagements found for this opportunity."}, status=status.HTTP_404_NOT_FOUND)

        for engagement in engagements:
            engagement.engagement_status = "completed"
            engagement.end_date = timezone.now().date()
            engagement.save()

        return Response({"message": "All engagements for this opportunity marked as completed."}, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Triggered when a volunteer wants to cancel their engagement, or an organization wnates to cancel a singular engagement.
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cancel_engagement_volunteer(request, volunteer_engagement_id):
    if request.method == "PATCH":
        try:
            engagement = VolunteerEngagement.objects.get(volunteer_engagement_id=volunteer_engagement_id)
        except VolunteerEngagement.DoesNotExist:
            return Response({"error": "Engagement not found."}, status=status.HTTP_404_NOT_FOUND)

        opportunity = engagement.volunteer_opportunity_application.volunteer_opportunity

        # Check if request user is either the volunteer or the organization that owns the opportunity
        is_volunteer = engagement.volunteer.account == request.user
        is_organization = opportunity.organization.account == request.user

        if not (is_volunteer or is_organization):
            return Response({"error": "Unauthorized to cancel this engagement."}, status=status.HTTP_403_FORBIDDEN)

        if engagement.engagement_status != "ongoing":
            return Response({"error": "Only ongoing engagements can be canceled."}, status=status.HTTP_400_BAD_REQUEST)

        # Re-increment slots if the opportunity has a limited number of slots
        if opportunity.slots is not None:
            slots_to_restore = 1 + engagement.volunteer_opportunity_application.no_of_additional_volunteers
            opportunity.slots += slots_to_restore
            opportunity.save()

        # Cancel engagement
        engagement.engagement_status = "cancelled"
        engagement.end_date = timezone.now().date()
        engagement.save()

        return Response({"message": "Engagement successfully canceled."}, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Triggered when an organization wants to cancel all engagements for a specific opportunity.
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cancel_engagements_organization(request, volunteer_opportunity_id):
    if request.method == "PATCH":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can cancel engagements."}, status=status.HTTP_403_FORBIDDEN)

        try:
            opportunity = VolunteerOpportunity.objects.get(volunteer_opportunity_id=volunteer_opportunity_id)
        except VolunteerOpportunity.DoesNotExist:
            return Response({"error": "Opportunity not found."}, status=status.HTTP_404_NOT_FOUND)

        if opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized to cancel engagements for this opportunity."}, status=status.HTTP_403_FORBIDDEN)

        engagements = VolunteerEngagement.objects.filter(volunteer_opportunity_application__volunteer_opportunity=opportunity)

        if not engagements.exists():
            return Response({"error": "No engagements found for this opportunity."}, status=status.HTTP_404_NOT_FOUND)

        for engagement in engagements:
            engagement.engagement_status = "cancelled"
            engagement.end_date = timezone.now().date()
            engagement.save()

        return Response({"message": "All engagements for this opportunity marked as cancelled."}, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_session(request, opportunity_id):
    if request.method == "POST":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can create sessions."}, status=status.HTTP_403_FORBIDDEN)

        try:
            opportunity = VolunteerOpportunity.objects.get(volunteer_opportunity_id=opportunity_id)
        except VolunteerOpportunity.DoesNotExist:
            return Response({"error": "Opportunity not found."}, status=status.HTTP_404_NOT_FOUND)

        if not opportunity.ongoing:
            return Response({"error": "Sessions can only be created for ongoing opportunities."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data["opportunity_id"] = opportunity.pk  # Ensure correct opportunity is linked

        serializer = VolunteerOpportunitySessionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Session created successfully.", "data": serializer.data}, status=status.HTTP_201_CREATED)

        return Response({"message": "Failed to create session.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sessions(request, opportunity_id):
    if request.method == "GET":
        try:
            opportunity = VolunteerOpportunity.objects.get(volunteer_opportunity_id=opportunity_id)
        except VolunteerOpportunity.DoesNotExist:
            return Response({"error": "Opportunity not found."}, status=status.HTTP_404_NOT_FOUND)

        sessions = VolunteerOpportunitySession.objects.filter(opportunity=opportunity)
        serializer = VolunteerOpportunitySessionSerializer(sessions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def complete_session(request, session_id):
    if request.method == "PATCH":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can complete sessions."}, status=status.HTTP_403_FORBIDDEN)

        try:
            session = VolunteerOpportunitySession.objects.get(session_id=session_id)
        except VolunteerOpportunitySession.DoesNotExist:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure only the organization that owns the parent opportunity can update
        if session.opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized to update this session."}, status=status.HTTP_403_FORBIDDEN)

        if session.status != "upcoming":
            return Response({"error": "Only upcoming sessions can be completed."}, status=status.HTTP_400_BAD_REQUEST)

        session.status = "completed"
        session.save()

        return Response({"message": "Session marked as completed."}, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cancel_session(request, session_id):
    if request.method == "PATCH":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can cancel sessions."}, status=status.HTTP_403_FORBIDDEN)

        try:
            session = VolunteerOpportunitySession.objects.get(session_id=session_id)
        except VolunteerOpportunitySession.DoesNotExist:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure only the organization that owns the parent opportunity can update
        if session.opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized to update this session."}, status=status.HTTP_403_FORBIDDEN)

        if session.status != "upcoming":
            return Response({"error": "Only upcoming sessions can be cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        session.status = "cancelled"
        session.save()

        return Response({"message": "Session successfully cancelled."}, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Creates session engagements for all engaged volunteers of the related opportunity
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_session_engagements_for_session(request, session_id):
    if request.method == "POST":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can create session engagements."}, status=status.HTTP_403_FORBIDDEN)
        try:
            session = VolunteerOpportunitySession.objects.get(session_id=session_id)
        except VolunteerOpportunitySession.DoesNotExist:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        if session.opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized to create session engagements for this session."}, status=status.HTTP_403_FORBIDDEN)

        # Get all volunteer engagements linked to the opportunity
        engagements = VolunteerEngagement.objects.filter(volunteer_opportunity_application__volunteer_opportunity=session.opportunity)

        # Create a session engagement for each engaged volunteer
        created_engagements = []
        for engagement in engagements:
            data = {
                "volunteer_engagement_id": engagement.pk,
                "session_id": session.pk,
                "status": "cant_go"
            }
            serializer = VolunteerSessionEngagementSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                created_engagements.append(serializer.data)

        return Response({"message": "Session engagements created successfully.", "data": created_engagements}, status=status.HTTP_201_CREATED)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
# Creates session engagements for all upcoming sessions when a volunteer is accepted
### THE ORGANIZATION IS GONNA TRIGGER THIS
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_session_engagements_for_volunteer(request, account_uuid, opportunity_id):
    if request.method == "POST":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can create session engagements."}, status=status.HTTP_403_FORBIDDEN)

        try:
            volunteer = Volunteer.objects.get(account__account_uuid=account_uuid)
        except Volunteer.DoesNotExist:
            return Response({"error": "Volunteer not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure the volunteer is engaged in the specific ongoing opportunity
        engagement = VolunteerEngagement.objects.filter(
            volunteer=volunteer, 
            volunteer_opportunity_application__volunteer_opportunity__volunteer_opportunity_id=opportunity_id,
            volunteer_opportunity_application__volunteer_opportunity__ongoing=True
        ).first()  # Get only the first (should be only one per opportunity)

        if not engagement:
            return Response({"error": "No valid engagement found for this ongoing opportunity."}, status=status.HTTP_404_NOT_FOUND)

        # Get all upcoming sessions for this specific opportunity
        sessions = VolunteerOpportunitySession.objects.filter(
            opportunity=engagement.volunteer_opportunity_application.volunteer_opportunity,
            session_date__gte=timezone.now().date(),
            status="upcoming"
        )

        created_session_engagements = []
        for session in sessions:
            data = {
                "volunteer_engagement_id": engagement.pk,
                "session_id": session.pk,
                "status": "cant_go"
            }
            serializer = VolunteerSessionEngagementSerializer(data=data, context={"request": request})
            if serializer.is_valid():
                serializer.save()
                created_session_engagements.append(serializer.data)

        return Response({"message": "Session engagements created successfully.", "data": created_session_engagements}, status=status.HTTP_201_CREATED)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Volunteer confirms attendance
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def confirm_attendance(request, session_engagement_id):
    if request.method == "PATCH":
        try:
            session_engagement = VolunteerSessionEngagement.objects.get(session_engagement_id=session_engagement_id)
        except VolunteerSessionEngagement.DoesNotExist:
            return Response({"error": "Session engagement not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if session_engagement.volunteer_engagement.volunteer.account != request.user:
            return Response({"error": "Unauthorized to confirm attendance for this session."}, status=status.HTTP_403_FORBIDDEN)

        serializer = VolunteerSessionEngagementSerializer(session_engagement, data={"status": "can_go"}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Attendance confirmed.", "data": serializer.data}, status=status.HTTP_200_OK)

        return Response({"message": "Failed to confirm attendance.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Volunteer cancels attendance
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cancel_attendance(request, session_engagement_id):
    if request.method == "PATCH":
        try:
            session_engagement = VolunteerSessionEngagement.objects.get(session_engagement_id=session_engagement_id)
        except VolunteerSessionEngagement.DoesNotExist:
            return Response({"error": "Session engagement not found."}, status=status.HTTP_404_NOT_FOUND)

        opportunity = session_engagement.session.opportunity

        # Check if request user is either the volunteer or the organization that owns the opportunity
        is_volunteer = session_engagement.volunteer_engagement.volunteer.account == request.user
        is_organization = opportunity.organization.account == request.user

        if not (is_volunteer or is_organization):
            return Response({"error": "Unauthorized to cancel attendance for this session."}, status=status.HTTP_403_FORBIDDEN)

        serializer = VolunteerSessionEngagementSerializer(session_engagement, data={"status": "cant_go"}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Attendance canceled.", "data": serializer.data}, status=status.HTTP_200_OK)

        return Response({"message": "Failed to cancel attendance.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Get all session engagements for a session
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_engagements(request, session_id):
    if request.method == "GET":
        try:
            session = VolunteerOpportunitySession.objects.get(session_id=session_id)
        except VolunteerOpportunitySession.DoesNotExist:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        if session.opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized to view session engagements."}, status=status.HTTP_403_FORBIDDEN)

        engagements = VolunteerSessionEngagement.objects.filter(session=session)
        serializer = VolunteerSessionEngagementSerializer(engagements, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Get all session engagements for a volunteer
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_volunteer_session_engagements(request, account_uuid):
    if request.method == "GET":
        try:
            volunteer = Volunteer.objects.get(account__account_uuid=account_uuid)
        except Volunteer.DoesNotExist:
            return Response({"error": "Volunteer not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get all session engagements related to the volunteer
        session_engagements = VolunteerSessionEngagement.objects.filter(
            volunteer_engagement__volunteer=volunteer
        )

        serializer = VolunteerSessionEngagementSerializer(session_engagements, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Creates engagement logs when an organization completes a one-time opportunity.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_opportunity_engagement_logs(request, opportunity_id):
    if request.method == "POST":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can create engagement logs."}, status=status.HTTP_403_FORBIDDEN)

        try:
            opportunity = VolunteerOpportunity.objects.get(volunteer_opportunity_id=opportunity_id)
        except VolunteerOpportunity.DoesNotExist:
            return Response({"error": "Opportunity not found."}, status=status.HTTP_404_NOT_FOUND)

        if opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized to create logs for this opportunity."}, status=status.HTTP_403_FORBIDDEN)

        if opportunity.ongoing:
            return Response({"error": "Logs for ongoing opportunities must be session-based."}, status=status.HTTP_400_BAD_REQUEST)

        engagements = VolunteerEngagement.objects.filter(volunteer_opportunity_application__volunteer_opportunity=opportunity, engagement_status="completed")

        created_logs = []
        for engagement in engagements:
            data = {
                "volunteer_engagement_id": engagement.pk,
                "no_of_hours": (opportunity.opportunity_time_to.hour - opportunity.opportunity_time_from.hour),
                "status": "approved",
                "log_notes": f"Contributed to {opportunity.organization.organization_name} at {opportunity.title}"
            }
            serializer = VolunteerEngagementLogSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                created_logs.append(serializer.data)

        return Response({"message": "Engagement logs created successfully.", "data": created_logs}, status=status.HTTP_201_CREATED)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Creates engagement logs when an organization completes a session for an ongoing opportunity.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_session_engagement_logs(request, session_id):
    if request.method == "POST":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can create session engagement logs."}, status=status.HTTP_403_FORBIDDEN)

        try:
            session = VolunteerOpportunitySession.objects.get(session_id=session_id)
        except VolunteerOpportunitySession.DoesNotExist:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        if session.opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized to create logs for this session."}, status=status.HTTP_403_FORBIDDEN)

        # Ensure it's an ongoing opportunity
        if not session.opportunity.ongoing:
            return Response({"error": "Only ongoing opportunities have session-based engagement logs."}, status=status.HTTP_400_BAD_REQUEST)

        # Only session engagements with status "can_go" are considered
        session_engagements = VolunteerSessionEngagement.objects.filter(session=session, status="can_go")

        created_logs = []
        for session_engagement in session_engagements:
            engagement = session_engagement.volunteer_engagement
            data = {
                "volunteer_engagement_id": engagement.pk,
                "session_id": session_engagement.pk,
                "no_of_hours": (session.session_end_time.hour - session.session_start_time.hour),
                "status": "approved",
                "log_notes": f"Contributed to {session.opportunity.organization.organization_name} at {session.title}"
            }
            serializer = VolunteerEngagementLogSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                created_logs.append(serializer.data)

        return Response({"message": "Session engagement logs created successfully.", "data": created_logs}, status=status.HTTP_201_CREATED)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


# Allows a volunteer to submit a log for an ongoing opportunity (Manual Log)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_engagement_log_volunteer(request, opportunity_id):
    if request.method == "POST":
        if not request.user.is_volunteer():
            return Response({"error": "Only volunteers can submit engagement logs."}, status=status.HTTP_403_FORBIDDEN)

        try:
            engagement = VolunteerEngagement.objects.get(
                volunteer_opportunity_application__volunteer_opportunity__volunteer_opportunity_id=opportunity_id,
                volunteer__account=request.user
            )
        except VolunteerEngagement.DoesNotExist:
            return Response({"error": "Engagement not found."}, status=status.HTTP_404_NOT_FOUND)

        if not engagement.volunteer_opportunity_application.volunteer_opportunity.ongoing:
            return Response({"error": "Logs for one-time opportunities must be system-generated."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data["volunteer_engagement_id"] = engagement.pk
        data["status"] = "pending"  # Logs submitted manually must be approved by an organization
        data["is_volunteer_request"] = True # Flag to indicate that this log was submitted by the volunteer

        serializer = VolunteerEngagementLogSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Engagement log submitted for approval.", "data": serializer.data}, status=status.HTTP_201_CREATED)

        return Response({"message": "Failed to submit log.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


# Organization approves a volunteer's engagement log
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def approve_engagement_log(request, volunteer_engagement_log_id):
    if request.method == "PATCH":
        try:
            log = VolunteerEngagementLog.objects.get(volunteer_engagement_log_id=volunteer_engagement_log_id)
        except VolunteerEngagementLog.DoesNotExist:
            return Response({"error": "Engagement log not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure only organizations can approve logs
        if not request.user.is_organization():
            return Response({"error": "Only organizations can approve engagement logs."}, status=status.HTTP_403_FORBIDDEN)

        serializer = VolunteerEngagementLogSerializer(log, data={"status": "approved"}, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Engagement log approved.", "data": serializer.data}, status=status.HTTP_200_OK)

        return Response({"message": "Failed to approve engagement log.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


# Organization rejects a volunteer's engagement log
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def reject_engagement_log(request, volunteer_engagement_log_id):
    if request.method == "PATCH":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can reject engagement logs."}, status=status.HTTP_403_FORBIDDEN)

        try:
            log = VolunteerEngagementLog.objects.get(volunteer_engagement_log_id=volunteer_engagement_log_id)
        except VolunteerEngagementLog.DoesNotExist:
            return Response({"error": "Engagement log not found."}, status=status.HTTP_404_NOT_FOUND)

        if log.volunteer_engagement.volunteer_opportunity_application.volunteer_opportunity.organization.account != request.user:
            return Response({"error": "Unauthorized to reject this engagement log."}, status=status.HTTP_403_FORBIDDEN)

        if log.status != "pending":
            return Response({"error": "Only pending engagement logs can be rejected."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VolunteerEngagementLogSerializer(log, data={"status": "rejected"}, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Engagement log rejected successfully."}, status=status.HTTP_200_OK)

        return Response({"message": "Failed to reject engagement log.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Fetch pending engagement logs for an organization's opportunities
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_organization_log_requests(request, account_uuid):
    if request.method == "GET":
        if not request.user.is_organization():
            return Response({"error": "Only organizations can view log requests."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            organization = Organization.objects.get(account__account_uuid=account_uuid)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found."}, status=status.HTTP_404_NOT_FOUND)
        
        pending_logs = VolunteerEngagementLog.objects.filter(
            volunteer_engagement__volunteer_opportunity_application__volunteer_opportunity__organization=organization,
            status="pending"
        )

        serializer = VolunteerEngagementLogSerializer(pending_logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    

# Fetch engagement logs for a volunteer on the profile page
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_engagement_logs(request, account_uuid):
    if request.method == "GET":
        try:
            volunteer = Volunteer.objects.get(account__account_uuid=account_uuid)
        except Volunteer.DoesNotExist:
            return Response({"error": "Volunteer not found."}, status=status.HTTP_404_NOT_FOUND)
        
        logs = VolunteerEngagementLog.objects.filter(volunteer_engagement__volunteer=volunteer, status="approved")
        serializer = VolunteerEngagementLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
# Fetch engagement logs for a volunteer which they have explicitly requested on engagements and applications page
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_volunteer_log_requests(request, account_uuid):
    if request.method == "GET":
        if not request.user.is_volunteer():
            return Response({"error": "Only volunteers can view their engagement log requests."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            volunteer = Volunteer.objects.get(account__account_uuid=account_uuid)
        except Volunteer.DoesNotExist:
            return Response({"error": "Volunteer not found."}, status=status.HTTP_404_NOT_FOUND)
        
        log_requests = VolunteerEngagementLog.objects.filter(
            volunteer_engagement__volunteer=volunteer,
            is_volunteer_request=True
        )
        serializer = VolunteerEngagementLogSerializer(log_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
