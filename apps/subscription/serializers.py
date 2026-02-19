from django.utils import timezone
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
    features = PackageFeatureSerializer(many=True, read_only=True)
    final_price = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    interval_display = serializers.CharField(source='get_interval_display', read_only=True)
    is_active = serializers.SerializerMethodField()
    stripe_subscription_id = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = [
            'id', 'name', 'tagline', 'price', 'final_price', 'price_display',
            'interval', 'interval_display', 'description', 'features',
            'is_popular', 'display_order', 'border_color', 'button_color',
            'button_text_color', 'discount', 'discount_price', 'is_active',
            'stripe_subscription_id',
        ]

    def get_final_price(self, obj):
        return float(obj.discount_price if obj.discount > 0 else obj.price)

    def get_price_display(self, obj):
        price = self.get_final_price(obj)
        return f'${int(price)}' if price == int(price) else f'${price:.2f}'

    # serializer cache for every request
    def _get_active_subscription(self, obj):
        if not hasattr(self, '_active_sub_cache'):
            self._active_sub_cache = {}

        if obj.pk in self._active_sub_cache:
            return self._active_sub_cache[obj.pk]

        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if not user or not user.is_authenticated:
            self._active_sub_cache[obj.pk] = None
            return None

        sub = Subscription.objects.filter(
            user=user,
            package=obj,
            is_active=True
        ).only('payment_method', 'stripe_subscription_id').first()

        self._active_sub_cache[obj.pk] = sub
        return sub

    def get_is_active(self, obj):
        return self._get_active_subscription(obj) is not None

    def get_stripe_subscription_id(self, obj):
        sub = self._get_active_subscription(obj)
        if sub and sub.payment_method == 'stripe':
            return sub.stripe_subscription_id
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # is_active False remove field
        if not representation.get('is_active'):
            representation.pop('stripe_subscription_id', None)

        return representation


class PricingSectionSerializer(serializers.ModelSerializer):
    packages = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = PricingSection
        fields = [
            'id', 'title', 'subtitle', 'background_color', 'text_color',
            'popular_badge_text', 'popular_badge_color', 
            'free_plan_button_text', 'paid_plan_button_text',
            'packages', 'is_active'
        ]
    
    def get_packages(self, obj):
        packages = Package.objects.filter(is_active=True).prefetch_related('features')
        return PackageCMSSerializer(packages, many=True).data
    
    def get_is_active(self, obj):
        return Subscription.objects.filter(
            is_active=True,
            package__is_active=True
        ).exists()


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
            'is_active',
            'billing_cycle',
            'features',
        ]

# Subscription Header
class SubscriptionHeaderSerializer(serializers.ModelSerializer):
    active_plan = serializers.SerializerMethodField(method_name='get_active_plan')
    start_date = serializers.DateTimeField(format="%b-%d, %Y", read_only=True)
    remaining = serializers.SerializerMethodField(method_name='get_remaining')
    end_date = serializers.DateTimeField(format="%b-%d, %Y", read_only=True)
    status = serializers.SerializerMethodField(method_name='get_status')

    class Meta:
        model = Subscription
        fields = [
            'id',
            'active_plan',
            'start_date',
            'remaining',
            'end_date',
            'status',
        ]

    def get_active_plan(self, obj):
        active_subscription = Subscription.objects.filter(user=obj.user, is_active=True).select_related('package').first()
        return active_subscription.package.name if active_subscription else None

    def get_remaining(self, obj):
        if obj.end_date:
            remaining_time = obj.end_date - timezone.now()
            return remaining_time.days
        return None

    def get_status(self, obj):
        if obj.is_active:
            return 'active'
        elif obj.end_date and obj.end_date < timezone.now():
            return 'expired'
        else:
            return 'inactive'
