const { Client, MessageMedia, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// ✅ Track current product
let currentProduct = null;

// ✅ Only these senders are allowed
const allowedSenders = [
    '919999888777@c.us', // Vendor
    '120363045678902@g.us', // Group
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
        const filename = saveImage(media);

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

        currentProduct.images.push(filename);
        console.log(`🖼️ Added image: ${filename}`);
    } else {
        if (!currentProduct) {
            console.log('⚠️ Text received without any image — ignoring.');
            return;
        }
        currentProduct.description += msg.body + '\n';
        console.log(`📝 Appended text: ${msg.body}`);
    }
});

// ✅ Save image
function saveImage(media) {
    const folder = path.join(__dirname, 'images');
    if (!fs.existsSync(folder)) fs.mkdirSync(folder);
    const filename = `img_${Date.now()}.jpg`;
    const filepath = path.join(folder, filename);
    fs.writeFileSync(filepath, Buffer.from(media.data, 'base64'));
    return filename;
}

// ✅ Send to Django
async function saveProduct(product) {
    try {
        console.log('🚀 Sending product to Django API...');
        console.log('Sender:', product.sender);
        console.log('Description:', product.description.trim());
        console.log('Images:', product.images);

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
