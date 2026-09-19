const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

const user = tg.initDataUnsafe?.user;

if (user) {
    const name = document.getElementById("user-name");

    if (name) {
        name.textContent = user.first_name;
    }

    const id = document.getElementById("user-id");

    if (id) {
        id.textContent = "ID: " + user.id;
    }

    const username = document.getElementById("user-username");

    if (username) {
        username.textContent = user.username
            ? "@" + user.username
            : "Без username";
    }

    const avatar = document.getElementById("user-avatar");

    if (avatar) {
        avatar.textContent =
            user.first_name.charAt(0).toUpperCase();
    }
}