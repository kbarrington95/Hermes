from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models.aggregates import Count
from rest_framework.generics import ListCreateAPIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Campaign
from .serializers import CampaignSerializer

@api_view()
def campaign_detail(request, id):
    campaign = get_object_or_404(Campaign.objects.annotate(
        sessions_count=Count('sessions')), pk=id)
    serializer = CampaignSerializer(campaign)

    return Response(serializer.data)

class CampaignList(ListCreateAPIView):
    queryset = Campaign.objects.annotate(sessions_count=Count('sessions')).all()
    serializer_class = CampaignSerializer