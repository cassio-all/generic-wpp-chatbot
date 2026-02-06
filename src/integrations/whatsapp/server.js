/**
 * WhatsApp Web Bridge Server
 * Connects WhatsApp Web.js with Python chatbot via WebSocket
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const WebSocket = require('ws');
const express = require('express');

const app = express();
const PORT = 8765;

// WebSocket server for Python communication
const wss = new WebSocket.Server({ port: PORT });
let pythonClient = null;

// WhatsApp client with persistent session
const whatsappClient = new Client({
    authStrategy: new LocalAuth({
        dataPath: './.wwebjs_auth'
    }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu'
        ]
    }
});

// WebSocket connection from Python
wss.on('connection', (ws) => {
    console.log('🐍 Python client connected');
    pythonClient = ws;
    
    // Send ready status
    if (whatsappClient.info) {
        sendToPython({
            type: 'status',
            status: 'ready',
            info: whatsappClient.info
        });
    }

    ws.on('message', async (data) => {
        try {
            const message = JSON.parse(data);
            await handlePythonMessage(message);
        } catch (error) {
            console.error('❌ Error handling Python message:', error);
            ws.send(JSON.stringify({
                type: 'error',
                error: error.message
            }));
        }
    });

    ws.on('close', () => {
        console.log('🐍 Python client disconnected');
        pythonClient = null;
    });
});

// Handle messages from Python
async function handlePythonMessage(message) {
    const { type, data } = message;

    switch (type) {
        case 'send_message':
            await sendWhatsAppMessage(data.to, data.text);
            break;
        
        case 'send_typing':
            await sendTyping(data.to);
            break;
        
        case 'get_chats':
            await getChats();
            break;
        
        case 'get_contact':
            await getContact(data.id);
            break;
        
        default:
            console.log('⚠️ Unknown message type:', type);
    }
}

// Send message via WhatsApp
async function sendWhatsAppMessage(to, text) {
    try {
        const chatId = to.includes('@c.us') ? to : `${to}@c.us`;
        
        // Don't send to broadcasts
        if (chatId === 'status@broadcast' || chatId.includes('broadcast')) {
            console.log('⚠️ Ignoring message to broadcast channel');
            return;
        }
        
        await whatsappClient.sendMessage(chatId, text);
        
        sendToPython({
            type: 'message_sent',
            to: chatId,
            success: true
        });
        
        console.log(`✅ Message sent to ${chatId.split('@')[0]}`);
    } catch (error) {
        console.error('❌ Error sending message:', error.message);
        sendToPython({
            type: 'message_sent',
            to: to,
            success: false,
            error: error.message
        });
    }
}

// Send typing indicator
async function sendTyping(to) {
    try {
        const chatId = to.includes('@c.us') ? to : `${to}@c.us`;
        
        // Don't send typing to broadcasts
        if (chatId === 'status@broadcast' || chatId.includes('broadcast')) {
            return;
        }
        
        const chat = await whatsappClient.getChatById(chatId);
        await chat.sendStateTyping();
    } catch (error) {
        // Silently fail - typing indicators are not critical
        console.debug('Could not send typing indicator');
    }
}

// Get all chats
async function getChats() {
    try {
        const chats = await whatsappClient.getChats();
        const chatList = chats.map(chat => ({
            id: chat.id._serialized,
            name: chat.name,
            isGroup: chat.isGroup,
            timestamp: chat.timestamp,
            unreadCount: chat.unreadCount
        }));
        
        sendToPython({
            type: 'chats_list',
            chats: chatList
        });
    } catch (error) {
        console.error('❌ Error getting chats:', error);
    }
}

// Get contact info
async function getContact(contactId) {
    try {
        const contact = await whatsappClient.getContactById(contactId);
        sendToPython({
            type: 'contact_info',
            contact: {
                id: contact.id._serialized,
                name: contact.name || contact.pushname,
                number: contact.number,
                isMyContact: contact.isMyContact
            }
        });
    } catch (error) {
        console.error('❌ Error getting contact:', error);
    }
}

// Send data to Python client
function sendToPython(data) {
    if (pythonClient && pythonClient.readyState === WebSocket.OPEN) {
        pythonClient.send(JSON.stringify(data));
    }
}

// WhatsApp client events
whatsappClient.on('qr', (qr) => {
    console.log('📱 QR Code received! Scan with WhatsApp:');
    qrcode.generate(qr, { small: true });
    
    sendToPython({
        type: 'qr_code',
        qr: qr
    });
});

whatsappClient.on('ready', () => {
    console.log('✅ WhatsApp client is ready!');
    console.log(`📱 Connected as: ${whatsappClient.info.pushname}`);
    console.log(`📞 Number: ${whatsappClient.info.wid.user}`);
    
    sendToPython({
        type: 'status',
        status: 'ready',
        info: {
            pushname: whatsappClient.info.pushname,
            number: whatsappClient.info.wid.user,
            platform: whatsappClient.info.platform
        }
    });
});

whatsappClient.on('authenticated', () => {
    console.log('🔐 WhatsApp authenticated successfully');
    sendToPython({
        type: 'status',
        status: 'authenticated'
    });
});

whatsappClient.on('auth_failure', (msg) => {
    console.error('❌ Authentication failure:', msg);
    sendToPython({
        type: 'status',
        status: 'auth_failure',
        error: msg
    });
});

whatsappClient.on('disconnected', (reason) => {
    console.log('❌ WhatsApp disconnected:', reason);
    sendToPython({
        type: 'status',
        status: 'disconnected',
        reason: reason
    });
});

whatsappClient.on('message', async (message) => {
    // Detect manual replies (from you) and notify Python to pause bot
    if (message.fromMe) {
        console.log('👤 Manual reply detected for:', message.to);
        sendToPython({
            type: 'manual_reply',
            contact: message.to  // The person you replied to
        });
        return;  // Don't process your own messages
    }
    
    // Ignore old messages (only process recent ones - last 30 seconds)
    const messageAge = (Date.now() / 1000) - message.timestamp;
    if (messageAge > 30) {
        console.log('⏳ Ignoring old message (age:', Math.round(messageAge), 'seconds)');
        return;
    }
    
    // Ignore status broadcasts (Stories) - silently
    if (message.from === 'status@broadcast' || message.from.includes('broadcast')) {
        return;
    }
    
    // Ignore group messages - silently (no log spam)
    if (message.from.includes('@g.us')) {
        return;
    }
    
    // Ignore channels/newsletters - silently (IDs start with 120363 or contain @newsletter)
    if (message.from.startsWith('120363') || message.from.includes('@newsletter')) {
        return;
    }
    
    // Ignore WhatsApp Business accounts and channels (@lid)
    if (message.from.includes('@lid')) {
        console.log('🏪 Ignoring WhatsApp Business/Channel:', message.from);
        return;
    }
    
    // Ignore empty messages
    if (!message.body && !message.hasMedia) {
        console.log('⚠️  Ignoring empty message from:', message.from);
        return;
    }
    
    // Truncate message for logs
    const bodyPreview = message.body.length > 50 ? 
        message.body.substring(0, 50) + '...' : 
        message.body;
    
    console.log(`📨 Message from ${message.from.split('@')[0]}: ${bodyPreview}`);
    
    // Get contact info
    const contact = await message.getContact();
    
    // Handle audio messages
    let audioData = null;
    if (message.hasMedia && message.type === 'ptt') {
        try {
            console.log('🎤 Downloading audio message...');
            const media = await message.downloadMedia();
            audioData = {
                mimetype: media.mimetype,
                data: media.data, // base64
                filename: media.filename || 'audio.ogg'
            };
            console.log('✅ Audio downloaded:', media.mimetype);
        } catch (error) {
            console.error('❌ Error downloading audio:', error.message);
        }
    }
    
    // Handle image messages
    let imageData = null;
    if (message.hasMedia && message.type === 'image') {
        try {
            console.log('🖼️  Downloading image message...');
            const media = await message.downloadMedia();
            imageData = {
                mimetype: media.mimetype,
                data: media.data, // base64
                filename: media.filename || 'image.jpg'
            };
            console.log('✅ Image downloaded:', media.mimetype);
        } catch (error) {
            console.error('❌ Error downloading image:', error.message);
        }
    }
    
    // Handle document messages (PDF, DOCX, etc)
    let documentData = null;
    if (message.hasMedia && message.type === 'document') {
        try {
            console.log('📄 Downloading document message...');
            const media = await message.downloadMedia();
            documentData = {
                mimetype: media.mimetype,
                data: media.data, // base64
                filename: media.filename || 'document.pdf'
            };
            console.log('✅ Document downloaded:', media.mimetype, '-', media.filename);
        } catch (error) {
            console.error('❌ Error downloading document:', error.message);
        }
    }
    
    // Check for unsupported media types
    if (message.hasMedia && !audioData && !imageData && !documentData) {
        console.log('⚠️  Unsupported media type:', message.type);
        // Override body to inform user
        message.body = `[Tipo de mídia não suportado: ${message.type}]`;
    }
    
    // Send to Python for processing
    sendToPython({
        type: 'incoming_message',
        message: {
            id: message.id._serialized,
            from: message.from,
            body: message.body,
            timestamp: message.timestamp,
            hasMedia: message.hasMedia,
            isGroup: message.from.includes('@g.us'),
            audio: audioData,
            image: imageData,
            document: documentData,
            contact: {
                name: contact.name || contact.pushname || contact.number,
                number: contact.number,
                isMyContact: contact.isMyContact
            }
        }
    });
});

whatsappClient.on('message_create', async (message) => {
    // Track our own sent messages
    if (message.fromMe) {
        console.log(`📤 Sent message to ${message.to}: ${message.body}`);
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    const status = {
        whatsapp: whatsappClient.info ? 'connected' : 'disconnected',
        python: pythonClient ? 'connected' : 'disconnected',
        uptime: process.uptime()
    };
    res.json(status);
});

app.listen(3000, () => {
    console.log('🌐 Health check server running on http://localhost:3000/health');
});

// Initialize WhatsApp client
console.log('🚀 Starting WhatsApp Bridge Server...');
console.log(`🔌 WebSocket server listening on port ${PORT}`);
console.log('⏳ Initializing WhatsApp client...');

whatsappClient.initialize();

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n👋 Shutting down gracefully...');
    await whatsappClient.destroy();
    wss.close();
    process.exit(0);
});
