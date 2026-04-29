
async function processData(items, options = {}) {
    const scale = options.scale || 1;
    console.log(`Processing ${items.length} items with scale ${scale}`);
    return items
        .filter(i => !i.invalid)
        .map(item => {
            const transformed = item.raw * scale;
            return { id: item.id, value: transformed, isEven: transformed % 2 === 0 };
        });
}

function logger(msg) { console.log("[LOG]: " + msg); }

class APIClient {
    constructor(url) { this.url = url; }
    async fetch(endpoint) {
        try {
            logger("Fetching from " + endpoint);
            const response = await fetch(this.url + endpoint);
            return await response.json();
        } catch (err) {
            logger("Error: " + err.message);
            return null;
        }
    }
}
