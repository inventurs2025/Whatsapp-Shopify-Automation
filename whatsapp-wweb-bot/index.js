const { Client, MessageMedia, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

// ✅ Track current product
let currentProduct = null;

// ✅ Only these senders are allowed
const allowedSenders = [
    '919999888777@c.us',
    '120363045678902@g.us',
    '917999563526@c.us',
    '917470860044@c.us',
];

// ✅ Setup WhatsApp client
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: false,
        args: ['--no-sandbox']
    }
});

// ✅ Show QR
client.on('qr', qr => {
    qrcode.generate(qr, { small: true });
    console.log('📱 Scan QR with WhatsApp');
});

client.on('ready', () => {
    console.log('✅ WhatsApp Connected!');
    console.log('📋 Flow: Multiple images → multiple texts → next image = next product');
});

client.on('message', async msg => {
    const senderId = msg.from;

    if (!allowedSenders.includes(senderId)) return;

    if (msg.hasMedia) {
        const media = await msg.downloadMedia();
        const filename = `img_${Date.now()}.jpg`;

        // ✅ Flush old product if it had description
        if (currentProduct && currentProduct.description.trim() !== '') {
            await saveProduct(currentProduct);
            currentProduct = null;
        }

        // ✅ Create new or add image to existing product
        if (!currentProduct) {
            currentProduct = {
                images: [],
                description: '',
                sender: senderId,
                timestamp: new Date().toISOString()
            };
        }

        // ✅ Push base64 image (no local file)
        currentProduct.images.push({
            filename: filename,
            base64: media.data,
            mimetype: media.mimetype
        });

        console.log(`🖼️ Added image (base64): ${filename}`);
    } else {
        if (!currentProduct) {
            console.log('⚠️ Text received without any image — ignoring.');
            return;
        }
        currentProduct.description += msg.body + '\n';
        console.log(`📝 Appended text: ${msg.body}`);
    }
});

// ✅ Send product to Django API
async function saveProduct(product) {
    try {
        console.log('🚀 Sending product to Django API...');
        console.log('Sender:', product.sender);
        console.log('Description:', product.description.trim());
        console.log('Images:', product.images.map(i => i.filename));

        const response = await axios.post('http://localhost:8000/api/add-product/', product);

        if (response.data.status === 'success') {
            console.log('✅ Product saved:', response.data.product_id);
        } else {
            console.log('❌ Save failed:', response.data.message);
        }
    } catch (err) {
        console.error('❌ Error:', err.message);
        if (err.response) {
            console.error('Response data:', err.response.data);
        }
    }
}

client.on('disconnected', reason => {
    console.log('❌ WhatsApp client disconnected:', reason);
});

// ✅ Start client
(async () => {
    console.log("🕐 Launching WhatsApp client...");
    await new Promise(resolve => setTimeout(resolve, 2000));
    client.initialize();
})();
