async function processData(items) {
    console.log("Processing " + items.length + " items...");
    return items.map(item => {
        return { id: item.id, value: item.raw * 2 };
    });
}
const validateUser = (user) => {
    if (!user.name) throw new Error("Missing name");
    return true;
};
class APIClient {
    constructor(url) { this.url = url; }
    async fetch(endpoint) {
        const response = await fetch(this.url + endpoint);
        return response.json();
    }
}