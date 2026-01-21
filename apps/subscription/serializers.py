from rest_framework import serializers
from .models import Package, Subscription, PackageFeature, PricingSection
from django.contrib.auth.models import User
from .models import PlanItem, Features

class PackageFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageFeature
        fields = ['id', 'feature_text', 'is_included', 'order']


class PackageSerializer(serializers.ModelSerializer):
    features = PackageFeatureSerializer(many=True, read_only=True)
    
    class Meta:
        model = Package
        fields = '__all__'


class PackageCMSSerializer(serializers.ModelSerializer):
    """Serializer for public pricing display"""
    features = PackageFeatureSerializer(many=True, read_only=True)
    final_price = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    interval_display = serializers.CharField(source='get_interval_display', read_only=True)
    
    class Meta:
        model = Package
        fields = [
            'id', 'name', 'tagline', 'price', 'final_price', 'price_display',
            'interval', 'interval_display', 'description', 'features',
            'is_popular', 'display_order', 'border_color', 'button_color',
            'button_text_color', 'discount', 'discount_price'
        ]
    
    def get_final_price(self, obj):
        return float(obj.discount_price if obj.discount > 0 else obj.price)
    
    def get_price_display(self, obj):
        price = self.get_final_price(obj)
        return f'${int(price)}' if price == int(price) else f'${price:.2f}'


class PricingSectionSerializer(serializers.ModelSerializer):
    packages = serializers.SerializerMethodField()
    
    class Meta:
        model = PricingSection
        fields = [
            'id', 'title', 'subtitle', 'background_color', 'text_color',
            'popular_badge_text', 'popular_badge_color', 
            'free_plan_button_text', 'paid_plan_button_text',
            'packages'
        ]
    
    def get_packages(self, obj):
        packages = Package.objects.filter(is_active=True).prefetch_related('features')
        return PackageCMSSerializer(packages, many=True).data


class SubscriptionSerializer(serializers.ModelSerializer):
    package = PackageSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Subscription
        fields = '__all__'

# Pricing Section
class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Features
        fields = [
            'id',
            'text',
            'included',
            'order',
        ]

class PlanItemSerializer(serializers.ModelSerializer):
    features = FeatureSerializer(many=True)
    class Meta:
        model = PlanItem
        fields = [
            'id',
            'name',
            'title',
            'price',
            'billing_cycle',
            'features',
        ]