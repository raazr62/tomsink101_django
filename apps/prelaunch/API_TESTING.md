# API Testing Guide - Pre-Launch Waitlist System

This guide provides example API calls you can use with tools like Postman, cURL, or your frontend application.

## Base URL
```
http://localhost:8000/api/prelaunch/
```

---

## 1. User Signup (Without Referral)

**Endpoint:** `POST /api/prelaunch/signup/`

**Request:**
```bash
curl -X POST http://localhost:8000/api/prelaunch/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com"
  }'
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Successfully joined the waitlist!",
  "data": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "referral_code": "john-doe-1a92bc",
    "referred_by": null,
    "referral_link": "http://localhost:8000/api/prelaunch/signup/?ref=john-doe-1a92bc",
    "referral_count": 0,
    "activated": false,
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

---

## 2. User Signup (With Referral)

**Endpoint:** `POST /api/prelaunch/signup/`

You can provide the referral code in **TWO WAYS**:

### Method 1: In Request Body
**Request:**
```bash
curl -X POST http://localhost:8000/api/prelaunch/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane@example.com",
    "referred_by": "john-doe-1a92bc"
  }'
```

### Method 2: As Query Parameter (Recommended for Links)
**Request:**
```bash
curl -X POST "http://localhost:8000/api/prelaunch/signup/?ref=john-doe-1a92bc" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane@example.com"
  }'
```

**Why Method 2?** When users click a referral link like:
```
https://yoursite.com/signup/?ref=john-doe-1a92bc
```
The frontend can POST to the same URL with the `?ref=` parameter intact, making it easier to track referrals automatically.

**Response (Success - Both Methods):**
```json
{
  "success": true,
  "message": "Successfully joined the waitlist!",
  "data": {
    "id": 2,
    "name": "Jane Smith",
    "email": "jane@example.com",
    "referral_code": "jane-smith-8e3f22",
    "referred_by": "john-doe-1a92bc",
    "referral_link": "http://localhost:8000/api/prelaunch/signup/?ref=jane-smith-8e3f22",
    "referral_count": 0,
    "activated": false,
    "created_at": "2025-01-15T11:00:00Z"
  }
}
```

**Note:** If both are provided, the `referred_by` in the body takes priority over the `ref` query parameter.

**Response (Email Already Exists):**
```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {
    "email": ["This email is already registered."]
  }
}
```

**Response (Invalid Referral Code):**
```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {
    "referred_by": ["Invalid referral code."]
  }
}
```

---

## 3. Get User Details by Referral Code

**Endpoint:** `GET /api/prelaunch/user/?code={referral_code}`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/prelaunch/user/?code=john-doe-1a92bc"
```

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "referral_code": "john-doe-1a92bc",
  "referred_by": null,
  "referral_link": "http://localhost:8000/api/prelaunch/signup/?ref=john-doe-1a92bc",
  "referral_count": 3,
  "referred_users": [
    {
      "name": "Jane Smith",
      "email": "jane@example.com",
      "created_at": "2025-01-15T11:00:00Z"
    },
    {
      "name": "Bob Johnson",
      "email": "bob@example.com",
      "created_at": "2025-01-15T12:00:00Z"
    },
    {
      "name": "Alice Williams",
      "email": "alice@example.com",
      "created_at": "2025-01-15T13:00:00Z"
    }
  ],
  "activated": false,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

## 4. Get User Details by Email

**Endpoint:** `GET /api/prelaunch/user/?email={email}`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/prelaunch/user/?email=john@example.com"
```

**Response:** Same as above

---

## 5. Get Leaderboard

**Endpoint:** `GET /api/prelaunch/leaderboard/?limit=10`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/prelaunch/leaderboard/?limit=10"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "referral_code": "john-doe-1a92bc",
      "referral_count": 25,
      "created_at": "2025-01-15T10:30:00Z"
    },
    {
      "rank": 2,
      "name": "Sarah Johnson",
      "email": "sarah@example.com",
      "referral_code": "sarah-johnson-7f9x12",
      "referral_count": 18,
      "created_at": "2025-01-15T09:00:00Z"
    },
    {
      "rank": 3,
      "name": "Mike Brown",
      "email": "mike@example.com",
      "referral_code": "mike-brown-3k8p45",
      "referral_count": 12,
      "created_at": "2025-01-15T11:30:00Z"
    }
  ]
}
```

---

## 6. Get Overall Statistics

**Endpoint:** `GET /api/prelaunch/stats/`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/prelaunch/stats/"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_signups": 150,
    "total_referrals": 75,
    "total_activated": 10,
    "top_referrers": [
      {
        "rank": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "referral_code": "john-doe-1a92bc",
        "referral_count": 25,
        "created_at": "2025-01-15T10:30:00Z"
      }
    ],
    "recent_signups": [
      {
        "id": 150,
        "name": "Latest User",
        "email": "latest@example.com",
        "referral_code": "latest-user-9x7k23",
        "referred_by": "john-doe-1a92bc",
        "referral_link": "http://localhost:8000/api/prelaunch/signup/?ref=latest-user-9x7k23",
        "referral_count": 0,
        "activated": false,
        "created_at": "2025-01-15T15:45:00Z"
      }
    ]
  }
}
```

---

## 7. Get User's Referrals

**Endpoint:** `GET /api/prelaunch/referrals/?code={referral_code}`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/prelaunch/referrals/?code=john-doe-1a92bc"
```

**Response:**
```json
{
  "success": true,
  "user": {
    "name": "John Doe",
    "email": "john@example.com",
    "referral_code": "john-doe-1a92bc",
    "referral_count": 3
  },
  "referrals": [
    {
      "id": 1,
      "parent_referral_code": "john-doe-1a92bc",
      "parent_name": "John Doe",
      "parent_email": "john@example.com",
      "child_email": "jane@example.com",
      "child_name": "Jane Smith",
      "created_at": "2025-01-15T11:00:00Z"
    },
    {
      "id": 2,
      "parent_referral_code": "john-doe-1a92bc",
      "parent_name": "John Doe",
      "parent_email": "john@example.com",
      "child_email": "bob@example.com",
      "child_name": "Bob Johnson",
      "created_at": "2025-01-15T12:00:00Z"
    },
    {
      "id": 3,
      "parent_referral_code": "john-doe-1a92bc",
      "parent_name": "John Doe",
      "parent_email": "john@example.com",
      "child_email": "alice@example.com",
      "child_name": "Alice Williams",
      "created_at": "2025-01-15T13:00:00Z"
    }
  ]
}
```

---

## 8. Check Referral Code

**Endpoint:** `GET /api/prelaunch/check-code/?code={referral_code}`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/prelaunch/check-code/?code=john-doe-1a92bc"
```

**Response (Valid):**
```json
{
  "success": true,
  "valid": true,
  "user": {
    "name": "John Doe",
    "referral_code": "john-doe-1a92bc"
  }
}
```

**Response (Invalid):**
```json
{
  "success": true,
  "valid": false,
  "message": "Invalid referral code."
}
```

---

## 9. Check Email Availability

**Endpoint:** `GET /api/prelaunch/check-email/?email={email}`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/prelaunch/check-email/?email=john@example.com"
```

**Response (Email Exists):**
```json
{
  "success": true,
  "exists": true,
  "message": "Email is already registered."
}
```

**Response (Email Available):**
```json
{
  "success": true,
  "exists": false,
  "message": "Email is available."
}
```

---

## 10. Fraud Detection (Admin Only)

**Endpoint:** `GET /api/prelaunch/fraud-detection/?ip={ip_address}`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/prelaunch/fraud-detection/?ip=192.168.1.1" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "suspicious_activity": [
      {
        "type": "Multiple accounts from same IP",
        "ip_address": "192.168.1.1",
        "count": 3,
        "users": [
          {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "referral_code": "john-doe-1a92bc",
            "created_at": "2025-01-15T10:30:00Z"
          },
          {
            "id": 5,
            "name": "Suspicious User",
            "email": "suspicious@example.com",
            "referral_code": "suspicious-user-4k9x21",
            "created_at": "2025-01-15T14:00:00Z"
          }
        ]
      }
    ]
  }
}
```

---

## Frontend Integration Examples

### React Example

```javascript
// SignupForm.jsx
import React, { useState, useEffect } from 'react';

function SignupForm() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [referralCode, setReferralCode] = useState('');
  const [userData, setUserData] = useState(null);

  // Capture referral code from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const ref = params.get('ref');
    if (ref) setReferralCode(ref);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      // Option 1: Send referral code in body
      const response = await fetch('http://localhost:8000/api/prelaunch/signup/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          email,
          referred_by: referralCode || undefined
        })
      });
      
      // Option 2: Send referral code as query param (Easier!)
      // const url = referralCode 
      //   ? `http://localhost:8000/api/prelaunch/signup/?ref=${referralCode}`
      //   : 'http://localhost:8000/api/prelaunch/signup/';
      // const response = await fetch(url, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ name, email })
      // });
      
      const data = await response.json();
      
      if (data.success) {
        setUserData(data.data);
        alert('Successfully joined the waitlist!');
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <button type="submit">Join Waitlist</button>
      </form>
      
      {userData && (
        <div className="success">
          <h3>Your Referral Link:</h3>
          <input 
            type="text" 
            value={userData.referral_link} 
            readOnly 
          />
          <p>Share this link to get referrals!</p>
        </div>
      )}
    </div>
  );
}

export default SignupForm;
```

### Vue Example

```vue
<template>
  <div>
    <form @submit.prevent="handleSubmit">
      <input
        v-model="name"
        type="text"
        placeholder="Name"
        required
      />
      <input
        v-model="email"
        type="email"
        placeholder="Email"
        required
      />
      <button type="submit">Join Waitlist</button>
    </form>
    
    <div v-if="userData" class="success">
      <h3>Your Referral Link:</h3>
      <input 
        :value="userData.referral_link" 
        readonly 
      />
      <p>Share this link to get referrals!</p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      name: '',
      email: '',
      referralCode: '',
      userData: null
    }
  },
  mounted() {
    // Capture referral code from URL
    const params = new URLSearchParams(window.location.search);
    const ref = params.get('ref');
    if (ref) this.referralCode = ref;
  },
  methods: {
    async handleSubmit() {
      try {
        const response = await fetch('http://localhost:8000/api/prelaunch/signup/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: this.name,
            email: this.email,
            referred_by: this.referralCode || undefined
          })
        });
        
        const data = await response.json();
        
        if (data.success) {
          this.userData = data.data;
          alert('Successfully joined the waitlist!');
        } else {
          alert(data.message);
        }
      } catch (error) {
        console.error('Error:', error);
      }
    }
  }
}
</script>
```

### Plain JavaScript Example

```javascript
// signup.js
document.addEventListener('DOMContentLoaded', function() {
  // Capture referral code from URL
  const urlParams = new URLSearchParams(window.location.search);
  const referralCode = urlParams.get('ref');
  
  const form = document.getElementById('signup-form');
  
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    
    try {
      const response = await fetch('http://localhost:8000/api/prelaunch/signup/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: name,
          email: email,
          referred_by: referralCode || undefined
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Show referral link
        document.getElementById('referral-link').value = data.data.referral_link;
        document.getElementById('success-message').style.display = 'block';
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred. Please try again.');
    }
  });
});
```

---

## Testing Workflow

### 1. Create First User
```bash
curl -X POST http://localhost:8000/api/prelaunch/signup/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Sarah Johnson", "email": "sarah@example.com"}'
```

### 2. Get User's Referral Code
Extract the `referral_code` from the response (e.g., `sarah-johnson-7f9x12`)

### 3. Create Second User with Referral
```bash
curl -X POST http://localhost:8000/api/prelaunch/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "referred_by": "sarah-johnson-7f9x12"
  }'
```

### 4. Check First User's Referrals
```bash
curl -X GET "http://localhost:8000/api/prelaunch/referrals/?code=sarah-johnson-7f9x12"
```

### 5. View Leaderboard
```bash
curl -X GET "http://localhost:8000/api/prelaunch/leaderboard/?limit=10"
```

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {
    "email": ["This field is required."]
  }
}
```

### 404 Not Found
```json
{
  "success": false,
  "message": "User not found."
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "message": "An error occurred during signup.",
  "error": "Error details here"
}
```

---

## Postman Collection

Import this into Postman for easy testing:

1. Create a new collection: "Pre-Launch Waitlist"
2. Add environment variable: `base_url` = `http://localhost:8000/api/prelaunch`
3. Create requests for each endpoint listed above
4. Use `{{base_url}}` in your URLs

---

## Rate Limiting (Optional)

To prevent spam, consider adding rate limiting in `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/hour',
    }
}
```
