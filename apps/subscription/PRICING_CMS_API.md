# Pricing CMS API Documentation

## Overview
The Pricing CMS API provides public endpoints to fetch pricing information for displaying on your frontend.

## Base URL
```
http://127.0.0.1:8000/api/subscription/
```

## Endpoints

### 1. Get Complete Pricing Section
**Endpoint:** `GET /api/subscription/pricing/`  
**Authentication:** None (Public)

Returns the complete pricing section with all packages and features.

**Response:**
```json
{
  "status": 200,
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Choose Your Plan",
    "subtitle": "Select the perfect plan for your goal-setting journey",
    "background_color": "#1a1a1a",
    "text_color": "#ffffff",
    "popular_badge_text": "Most Popular",
    "popular_badge_color": "#d4ff00",
    "free_plan_button_text": "Get Started Free",
    "paid_plan_button_text": "Get Started",
    "packages": [
      {
        "id": 1,
        "name": "Starter",
        "tagline": "Perfect for trying out GoalAI",
        "price": "0.00",
        "final_price": 0.0,
        "price_display": "$0",
        "interval": "month",
        "interval_display": "Monthly",
        "description": "Get started with basic goal tracking",
        "features": [
          {
            "id": "uuid",
            "feature_text": "1 Active Goal",
            "is_included": true,
            "order": 0
          },
          {
            "id": "uuid",
            "feature_text": "Basic AI Coaching",
            "is_included": true,
            "order": 1
          }
        ],
        "is_popular": false,
        "display_order": 1,
        "border_color": "#4a4a4a",
        "button_color": "#ffffff",
        "button_text_color": "#000000",
        "discount": "0.00",
        "discount_price": "0.00"
      },
      {
        "id": 2,
        "name": "Pro",
        "tagline": "For serious goal achievers",
        "price": "19.00",
        "final_price": 19.0,
        "price_display": "$19",
        "interval": "month",
        "interval_display": "Monthly",
        "is_popular": true,
        "features": [...]
      },
      {
        "id": 3,
        "name": "Enterprise",
        "tagline": "For teams and organizations",
        "price": "49.00",
        "final_price": 49.0,
        "price_display": "$49",
        "is_popular": false,
        "features": [...]
      }
    ]
  }
}
```

### 2. Get All Packages
**Endpoint:** `GET /api/subscription/pricing/packages/`  
**Authentication:** None (Public)

Returns only the packages without the pricing section wrapper.

**Response:**
```json
{
  "status": 200,
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Starter",
      "tagline": "Perfect for trying out GoalAI",
      "price": "0.00",
      "final_price": 0.0,
      "price_display": "$0",
      "interval": "month",
      "interval_display": "Monthly",
      "features": [...]
    }
  ]
}
```

### 3. Get Single Package
**Endpoint:** `GET /api/subscription/pricing/packages/{package_id}/`  
**Authentication:** None (Public)

Returns details of a specific package.

**Response:**
```json
{
  "status": 200,
  "success": true,
  "data": {
    "id": 2,
    "name": "Pro",
    "tagline": "For serious goal achievers",
    "price": "19.00",
    "final_price": 19.0,
    "price_display": "$19",
    "interval": "month",
    "interval_display": "Monthly",
    "description": "Unlock advanced features and unlimited goals",
    "features": [
      {
        "id": "uuid",
        "feature_text": "5 Active Goals",
        "is_included": true,
        "order": 0
      }
    ],
    "is_popular": true,
    "display_order": 2,
    "border_color": "#d4ff00",
    "button_color": "#d4ff00",
    "button_text_color": "#000000"
  }
}
```

## Frontend Usage Example

### React/Next.js
```javascript
// Fetch pricing data
async function getPricing() {
  const response = await fetch('http://127.0.0.1:8000/api/subscription/pricing/');
  const data = await response.json();
  return data.data;
}

// Component
function PricingSection() {
  const [pricing, setPricing] = useState(null);

  useEffect(() => {
    getPricing().then(setPricing);
  }, []);

  if (!pricing) return <div>Loading...</div>;

  return (
    <div style={{ backgroundColor: pricing.background_color, color: pricing.text_color }}>
      <h2>{pricing.title}</h2>
      <p>{pricing.subtitle}</p>
      
      <div className="packages-grid">
        {pricing.packages.map(pkg => (
          <div 
            key={pkg.id} 
            style={{ borderColor: pkg.border_color }}
            className={pkg.is_popular ? 'popular' : ''}
          >
            {pkg.is_popular && (
              <span 
                className="badge" 
                style={{ backgroundColor: pricing.popular_badge_color }}
              >
                {pricing.popular_badge_text}
              </span>
            )}
            
            <h3>{pkg.name}</h3>
            <p>{pkg.tagline}</p>
            <div className="price">{pkg.price_display}/{pkg.interval_display}</div>
            
            <ul>
              {pkg.features.map(feature => (
                <li key={feature.id}>
                  {feature.is_included && '✓'} {feature.feature_text}
                </li>
              ))}
            </ul>
            
            <button 
              style={{ 
                backgroundColor: pkg.button_color, 
                color: pkg.button_text_color 
              }}
            >
              {pkg.price == 0 ? pricing.free_plan_button_text : pricing.paid_plan_button_text}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Admin Management

Access the Django admin to manage:
- **Pricing Section:** `/admin/subscription/pricingsection/`
- **Packages:** `/admin/subscription/package/`
- **Package Features:** `/admin/subscription/packagefeature/`

### Adding Features to a Package
1. Go to Package in admin
2. Click on a package
3. Use the inline "Package features" section to add/edit features
4. Set the order to control display sequence

### Marking a Package as Popular
1. Go to Package in admin
2. Check "Is popular" checkbox
3. The package will show with the "Most Popular" badge

### Customizing Colors
All colors are customizable in the admin:
- Package border color
- Button colors (background and text)
- Section background and text colors
- Popular badge color

## Notes
- Only one `PricingSection` can be active at a time
- Packages are ordered by `display_order` field
- All endpoints are public (no authentication required)
- Features within a package are ordered by the `order` field
