const { Client, MessageMedia, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const SEPARATOR_EMOJI = '✅';
let currentProduct = null;
let currentVendor = 'DEFAULT';
const knownVendors = new Set();

const allowedSenders = [
    // '919999888777@c.us',
    // '120363045678902@g.us',
    '917999563526@c.us',
    '917000393711@c.us',
];

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: false,
        args: ['--no-sandbox']
    }
});

client.on('qr', qr => {
    qrcode.generate(qr, { small: true });
    console.log('📱 Scan QR with WhatsApp');
});

client.on('ready', () => {
    console.log('✅ WhatsApp Connected!');
});

client.on('message', async msg => {
    const senderId = msg.from;
    if (!allowedSenders.includes(senderId)) return;

    const body = msg.body.trim();

    // Vendor switch
    if (/vendor\s+/i.test(body)) {
        const newVendor = body.split(/\s+/)[1]?.toUpperCase();
        if (newVendor) {
            if (!knownVendors.has(newVendor)) {
                knownVendors.add(newVendor);
                await createVendorInShopify(newVendor);
            }
            currentVendor = newVendor;
            console.log(`👔 Switched to vendor: ${currentVendor}`);
            return;
        }
    }

    // Separator emoji = flush
    if (body.includes(SEPARATOR_EMOJI)) {
        if (currentProduct && currentProduct.description.trim() !== '') {
            await saveProduct(currentProduct);
            currentProduct = null;
        }
        return;
    }

    if (msg.hasMedia) {
        const media = await msg.downloadMedia();
        const filename = `img_${Date.now()}.jpg`;

        if (!currentProduct) {
            currentProduct = {
                images: [],
                description: '',
                sender: senderId,
                timestamp: new Date().toISOString(),
                vendor: currentVendor
            };
        }

        currentProduct.images.push({
            filename,
            base64: media.data,
            mimetype: media.mimetype
        });
        console.log(`🖼️ Added image: ${filename}`);
    } else {
        if (!currentProduct) return;
        currentProduct.description += body + '\n';
        console.log(`📝 Appended text: ${body}`);
    }
});

async function saveProduct(product) {
    try {
        const response = await axios.post('http://localhost:8000/api/add-product/', product);
        if (response.data.status === 'success') {
            console.log('✅ Product uploaded to Shopify.');
            await client.sendMessage(product.sender, `✅ Product uploaded to Shopify.`);
        } else {
            console.log('❌ Save failed:', response.data.message);
        }
    } catch (err) {
        console.error('❌ Error uploading product:', err.message);
    }
}

async function createVendorInShopify(vendorCode) {
    console.log(`🧾 Creating vendor in Shopify: ${vendorCode}`);
    // Note: Shopify does not have a vendor creation API. This is logical handling only.
}

client.on('disconnected', reason => {
    console.log('❌ WhatsApp client disconnected:', reason);
});

(async () => {
    console.log("🕐 Launching WhatsApp client...");
    await new Promise(resolve => setTimeout(resolve, 2000));
    client.initialize();
})();
