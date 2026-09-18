const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

console.log("Mini App запущено");

const user = tg.initDataUnsafe?.user;

if (user) {

    // Имя
    const name = document.getElementById("user-name");

    if (name) {
        name.textContent = user.first_name;
    }

    // Telegram ID
    const id = document.getElementById("user-id");

    if (id) {
        id.textContent = "ID: " + user.id;
    }

    // Username
    const username = document.getElementById("user-username");

    if (username) {
        username.textContent = user.username
            ? "@" + user.username
            : "Без username";
    }

}
