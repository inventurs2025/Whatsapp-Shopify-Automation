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
        console.log('❌ Test 1 Failed:', error.response?.data || error.message);
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
        console.log('✅ Test 2 correctly failed:', error.response?.data?.message);
    }
    
    // Test 3: Get all products
    console.log('\n📦 Test 3: Get all products');
    try {
        const response3 = await axios.get('http://localhost:8000/api/get-products/');
        console.log('✅ Test 3 Result:', response3.data);
        console.log('Total products:', response3.data.products.length);
    } catch (error) {
        console.log('❌ Test 3 Failed:', error.response?.data || error.message);
    }
}

// Run the test
testProductFlow().catch(console.error); 