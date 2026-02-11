from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models.aggregates import Count
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Product, Collection
from .serializers import ProductSerializers, CollectionSerializer



class ProductList(ListCreateAPIView):
    queryset = Product.objects.select_related('collection').all()
    serializer_class = ProductSerializers
    
    def get_serializer_context(self):
        return {'request': self.request}
    

class ProductDetail(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializers

    def delete(self, request, pk):
         product = get_object_or_404(Product, pk=pk)
         if product.orderitem_set.count() > 0: # type: ignore
            return Response({'error':'Cannot delete, This Product is a part of an existing Order'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
         product.delete()
         return Response(status=status.HTTP_204_NO_CONTENT)
    
# class ProductDetail(APIView):
#     def get(self, request, id):
#         product = get_object_or_404(Product, pk=id)
#         serializer = ProductSerializers(product)
#         return Response(serializer.data)
    
#     def put(self, request, id):
#         product = get_object_or_404(Product, pk=id)
#         serializer = ProductSerializers(product, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#     def delete(self, request, id):
#          product = get_object_or_404(Product, pk=id)
#          if product.orderitem_set.count() > 0: # type: ignore
#             return Response({'error':'Cannot delete, This Product is a part of an existing Order'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#          product.delete()
#          return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionList(ListCreateAPIView):
    queryset = Collection.objects.annotate(products_count=Count('products')).all()
    serializer_class = CollectionSerializer
    
# @api_view(['GET', 'POST'])
# def collection_list(request):
#     if request.method == 'GET':
#         queryset = Collection.objects.annotate(products_count=Count('products')).all()
#         serializer = CollectionSerializer(queryset, many=True)
#         return Response(serializer.data)
#     elif request.method == 'POST':
#         serializer = CollectionSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)

class CollectionDetail(RetrieveUpdateDestroyAPIView):
    queryset = Collection.objects.annotate(products_count=Count('products'))
    serializer_class = CollectionSerializer

    def delete(self, request, pk):
         collection = get_object_or_404(Collection, pk=pk)
         if collection.products.count() > 0: # type: ignore
            return Response({'error':'Cannot delete, This Collection has one or more Products'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
         collection.delete()
         return Response(status=status.HTTP_204_NO_CONTENT)
    