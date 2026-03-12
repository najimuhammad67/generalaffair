const {
    default: makeWASocket,
    useMultiFileAuthState,
    disconnectReason,
    fetchLatestBaileysVersion,
    delay
} = require('@whiskeysockets/baileys');
const pino = require('pino');
const express = require('express');
const qrcode = require('qrcode');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());
app.use(cors());

let sock;
let qrCodeData = null;
let isConnected = false;

const AUTH_PATH = path.join(__dirname, 'auth_info');

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_PATH);
    const { version } = await fetchLatestBaileysVersion();

    sock = makeWASocket({
        version,
        printQRInTerminal: true,
        auth: state,
        logger: pino({ level: 'silent' })
    });

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr) {
            qrCodeData = qr;
        }

        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect.error)?.output?.statusCode !== disconnectReason.loggedOut;
            isConnected = false;
            console.log('Connection closed due to', lastDisconnect.error, ', reconnecting:', shouldReconnect);
            if (shouldReconnect) {
                connectToWhatsApp();
            }
        } else if (connection === 'open') {
            console.log('WhatsApp connected successfully!');
            isConnected = true;
            qrCodeData = null;
        }
    });

    sock.ev.on('creds.update', saveCreds);
}

/**
 * Fungsi utama untuk mengirim notifikasi
 * @param {string} phone - Nomor HP (contoh: 62812345678)
 * @param {string} message - Isi pesan
 * @returns {Object} - Result status dan fallback link jika gagal
 */
async function sendNotification(phone, message) {
    // 1. Format nomor ke format WhatsApp (misal: 62812345678@s.whatsapp.net)
    let formattedPhone = phone.replace(/\D/g, ''); // Hapus karakter non-digit
    if (formattedPhone.startsWith('0')) {
        formattedPhone = '62' + formattedPhone.slice(1);
    }
    const jid = `${formattedPhone}@s.whatsapp.net`;
    const fallbackLink = `https://wa.me/${formattedPhone}`;

    if (!isConnected) {
        return { success: false, method: 'fallback', link: fallbackLink, reason: 'Bot not connected' };
    }

    try {
        // 2. Cek apakah nomor ada di WhatsApp
        const [result] = await sock.onWhatsApp(jid);
        
        if (result && result.exists) {
            // 3. Kirim pesan jika nomor terdaftar
            await sock.sendMessage(jid, { text: message });
            return { success: true, method: 'baileys', phone: formattedPhone };
        } else {
            // 4. Jika tidak ada, kembalikan fallback
            return { success: false, method: 'fallback', link: fallbackLink, reason: 'Number not on WhatsApp' };
        }
    } catch (error) {
        console.error('Error sending WhatsApp message:', error);
        return { success: false, method: 'fallback', link: fallbackLink, reason: error.message };
    }
}

// --- API Endpoints ---

// Endpoint untuk cek status & ambil QR
app.get('/api/status', (req, res) => {
    res.json({
        connected: isConnected,
        qr_pending: !!qrCodeData
    });
});

// Endpoint untuk generate QR Image
app.get('/api/qr', async (req, res) => {
    if (qrCodeData) {
        const qrImage = await qrcode.toDataURL(qrCodeData);
        res.send(`<img src="${qrImage}" style="display:block;margin:auto;margin-top:50px;">`);
    } else if (isConnected) {
        res.send('<h1>WhatsApp is already connected!</h1>');
    } else {
        res.send('<h1>Initializing... Please refresh in a few seconds</h1>');
    }
});

// Endpoint Utama untuk Kirim Notifikasi
app.post('/api/send', async (req, res) => {
    const { phone, message } = req.body;

    if (!phone || !message) {
        return res.status(400).json({ error: 'Phone and message are required' });
    }

    const result = await sendNotification(phone, message);
    res.json(result);
});

const PORT = 3001;
app.listen(PORT, () => {
    console.log(`WA Service running on http://localhost:${PORT}`);
    connectToWhatsApp();
});