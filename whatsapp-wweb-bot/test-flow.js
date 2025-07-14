const axios = require('axios');

// Test the product flow
async function testProductFlow() {
    console.log('🧪 Testing Product Flow...\n');
    
    // Test 1: Product with images and description
    console.log('📦 Test 1: Complete Product');
    const product1 = {
        sender: '919999888777@c.us',
        description: 'Beautiful red dress\nSize: M\nPrice: $50',
        images: ['img_1752298196229.jpg', 'img_1752298215146.jpg'],
        timestamp: new Date().toISOString()
    };
    
    try {
        const response1 = await axios.post('http://localhost:8000/api/add-product/', product1);
        console.log('✅ Test 1 Result:', response1.data);
    } catch (error) {
        console.log('❌ Test 1 Failed:', error.response?.data || error.message, error.response?.status || '');
    }
    
    // Test 2: Product with only images (should fail validation)
    console.log('\n📦 Test 2: Product with only images (should fail)');
    const product2 = {
        sender: '919999888777@c.us',
        description: '',
        images: ['img_1752298264241.jpg'],
        timestamp: new Date().toISOString()
    };
    
    try {
        const response2 = await axios.post('http://localhost:8000/api/add-product/', product2);
        console.log('❌ Test 2 should have failed but succeeded:', response2.data);
    } catch (error) {
        console.log('✅ Test 2 correctly failed:', error.response?.data || error.message, error.response?.status || '');
    }
    
    // Test 3: Get all products
    console.log('\n📦 Test 3: Get all products');
    try {
        const response3 = await axios.get('http://localhost:8000/api/get-products/');
        console.log('✅ Test 3 Result:', response3.data);
        console.log('Total products:', response3.data.products.length);
    } catch (error) {
        console.log('❌ Test 3 Failed:', error.response?.data || error.message, error.response?.status || '');
    }
}

// After Test 3, fetch the latest product from Shopify and print all its fields
async function fetchLatestShopifyProduct() {
    try {
        const shopifyDomain = process.env.SHOPIFY_STORE_DOMAIN || 'your-shop.myshopify.com';
        const apiKey = process.env.SHOPIFY_API_KEY || 'your_api_key';
        const apiPassword = process.env.SHOPIFY_API_PASSWORD || 'your_api_password';
        const url = `https://${shopifyDomain}/admin/api/2024-01/products.json?limit=1&order=created_at desc`;
        const response = await axios.get(url, {
            auth: { username: apiKey, password: apiPassword },
            headers: { 'Content-Type': 'application/json' }
        });
        const product = response.data.products[0];
        console.log('\n🛒 Latest Shopify Product:');
        console.dir(product, { depth: null });
        // Fetch metafields
        const metafieldsUrl = `https://${shopifyDomain}/admin/api/2024-01/products/${product.id}/metafields.json`;
        const metafieldsResp = await axios.get(metafieldsUrl, {
            auth: { username: apiKey, password: apiPassword },
            headers: { 'Content-Type': 'application/json' }
        });
        console.log('\n🔑 Metafields:');
        console.dir(metafieldsResp.data.metafields, { depth: null });
        // Fetch collects (collections)
        const collectsUrl = `https://${shopifyDomain}/admin/api/2024-01/collects.json?product_id=${product.id}`;
        const collectsResp = await axios.get(collectsUrl, {
            auth: { username: apiKey, password: apiPassword },
            headers: { 'Content-Type': 'application/json' }
        });
        console.log('\n📚 Collections (Collects):');
        console.dir(collectsResp.data.collects, { depth: null });
    } catch (error) {
        console.log('❌ Shopify fetch failed:', error.response?.data || error.message, error.response?.status || '');
    }
}

// Run the test
testProductFlow().catch(console.error); 
// Run the fetch after all tests
fetchLatestShopifyProduct(); 