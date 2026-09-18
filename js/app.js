const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

console.log("Mini App запущено");

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

}
