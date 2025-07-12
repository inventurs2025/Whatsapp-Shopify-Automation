# WhatsApp Shopify Automation

This project automates product collection from WhatsApp messages and stores them in a Django backend for Shopify integration.

## 🚀 Fixed Flow

### How It Works Now

1. **Vendor sends images** → Bot starts collecting images for a product
2. **Vendor sends description** → Bot adds text to the current product
3. **Vendor sends more images** → Bot saves the completed product and starts a new one
4. **Timeout protection** → Incomplete products are saved after 5 minutes

### Message Flow Example

```
Vendor: [Image 1] → Bot: "🆕 Started new product"
Vendor: [Image 2] → Bot: "📸 Added image: img_123.jpg (Total: 2)"
Vendor: "Beautiful red dress" → Bot: "📝 Added description: Beautiful red dress"
Vendor: "Size: M, Price: $50" → Bot: "📝 Added description: Size: M, Price: $50"
Vendor: [Image 3] → Bot: "💾 Saving completed product and starting new one..."
```

## 🔧 Setup Instructions

### 1. Django Backend Setup

```bash
cd whatsapp_django_api
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 2. WhatsApp Bot Setup

```bash
cd whatsapp-wweb-bot
npm install
node index.js
```

### 3. Configure Allowed Senders

Edit `whatsapp-wweb-bot/index.js` and update the `allowedSenders` array:

```javascript
const allowedSenders = [
    '919999888777@c.us',  // Individual chat
    '120363045678902@g.us', // Group chat
    // Add your allowed numbers/groups here
];
```

## 📋 API Endpoints

### Add Product
- **POST** `/api/add-product/`
- **Body**: `{ sender, description, images, timestamp }`

### Get Products
- **GET** `/api/get-products/`
- **Returns**: All saved products

## 🧪 Testing

Run the test script to verify the flow:

```bash
cd whatsapp-wweb-bot
node test-flow.js
```

## 🔍 Key Fixes Made

### 1. **Fixed Product Detection Logic**
- **Before**: Only saved products when new image arrived AND description existed
- **After**: Saves completed products when new image arrives, starts fresh product

### 2. **Added Database Model**
- Created `Product` model to persist data
- Added proper validation and error handling

### 3. **Improved Message Handling**
- Separate functions for media and text messages
- Better logging and error handling
- Group vs individual chat detection

### 4. **Added Timeout Protection**
- 5-minute timeout for incomplete products
- Prevents data loss from incomplete submissions

### 5. **Enhanced Validation**
- Requires images, description, and sender
- Proper error responses with meaningful messages

## 📊 Database Schema

```sql
Product:
- id (Primary Key)
- sender (CharField) - WhatsApp sender ID
- description (TextField) - Product description
- images (JSONField) - Array of image filenames
- timestamp (DateTimeField) - When product was created
- created_at (DateTimeField) - Database record creation time
```

## 🚨 Troubleshooting

### Common Issues

1. **Bot not responding**: Check if sender is in `allowedSenders` list
2. **Images not saving**: Ensure `images/` folder exists and is writable
3. **Django connection error**: Make sure Django server is running on port 8000
4. **QR code not scanning**: Check WhatsApp Web connection

### Debug Mode

The bot provides detailed logging:
- 📩 Message received
- 🖼️ Media processing
- 📝 Text processing
- 💾 Product saving
- ❌ Error messages

## 🔐 Security Notes

- Only process messages from allowed senders
- Images are saved locally (consider cloud storage for production)
- No authentication on API endpoints (add for production)
- CORS is enabled for all origins (restrict for production)

## 📈 Next Steps

1. Add Shopify API integration
2. Implement image upload to cloud storage
3. Add user authentication
4. Create web dashboard for product management
5. Add product categories and tags
6. Implement bulk operations 