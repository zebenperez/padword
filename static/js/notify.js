document.addEventListener('DOMContentLoaded', function() 
    {
        navigator.serviceWorker.register('/static/js/sw.js');
        Notification.requestPermission(function(result) {
            if (result === 'granted') {
                navigator.serviceWorker.ready.then(function(registration) {
                    registration.showNotification('Notification with ServiceWorker');
                });
            }
        });
    }); 
function sendNotify(title,desc,url)
{
    if (Notification.permission !== "granted")
    {
        Notification.requestPermission();
    }
    else
    {
        options = {
            "body": desc,
            "icon": "https://projects.shidix.es/static/chat/images/logo-blanco.png",
            "vibrate": [200, 100, 200, 100, 200, 100, 400],
            "tag": "request"
        }
        var notification = new Notification(title, options);
        /* Remove the notification from Notification Center when clicked.*/
        notification.onclick = function () {
            window.open(url);
        };

        /* Callback function when the notification is closed. */
        notification.onclose = function () {
            console.log('Notification closed');
        };
    }
}

function checkNotify()
{
    fetch('https://padword.shidix.es/bookings/bookings/notifications/').then(response => response.json()).then(data => sendNotify('Hay ' + data + 'peticiones pendientes', '', '/bookings/bookings/'));
    setTimeout(checkNotify, 300000);
}

