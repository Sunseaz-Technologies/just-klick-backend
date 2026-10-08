importScripts(
  "https://www.gstatic.com/firebasejs/10.13.2/firebase-app-compat.js"
);

importScripts(
  "https://www.gstatic.com/firebasejs/10.13.2/firebase-messaging-compat.js"
);

firebase.initializeApp({
    apiKey: "AIzaSyBYPM5TzyjENpMTGA455KrsqtnDH3MYdpU",
    authDomain: "justklick-500612.firebaseapp.com",
    projectId: "justklick-500612",
    storageBucket: "justklick-500612.firebasestorage.app",
    messagingSenderId: "481533763438",
    appId: "1:481533763438:web:ede7866bf12f2a34b16b7f"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
    self.registration.showNotification(
        payload.notification.title,
        {
            body: payload.notification.body
        }
    );
});
