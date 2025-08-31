document.addEventListener("DOMContentLoaded", function () {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");

    function appendMessage(text, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add(sender === "user" ? "user-message" : "bot-message");
        messageDiv.innerHTML = text;  // Using innerHTML to allow links and buttons
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function sendMessage() {
        let message = userInput.value.trim();
        if (!message) return;

        appendMessage(message, "user");
        userInput.value = "";

        try {
            const response = await fetch(`/get_product?product=${encodeURIComponent(message)}`);
            const data = await response.json();

            let botResponse = "";

            if (data.error) {
                botResponse = "Product not found.";
            } else if (data.message) {
                botResponse = data.message;  // For order tracking messages
            } else {
                botResponse = `
                    <strong>Product:</strong> ${data.product}<br>
                    <strong>Price:</strong> ₹${data.price}<br>
                    <strong>Stock:</strong> ${data.stock}<br>
                    <a href="${data.link}" target="_blank">
                        <button class="buy-btn">Buy</button>
                    </a>
                    <button class="cart-btn" onclick="addToCart('${data.product}')">Add to Cart</button>
                `;
            }

            appendMessage(botResponse, "bot");
        } catch (error) {
            appendMessage("Error connecting to the server.", "bot");
        }
    }

    async function addToCart(productName) {
        try {
            const response = await fetch(`https://farm2bag.com/api/add-to-cart`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ product: productName })
            });

            const result = await response.json();
            if (result.success) {
                appendMessage(`✅ ${productName} has been added to your cart!`, "bot");
            } else {
                appendMessage(`❌ Failed to add ${productName} to cart.`, "bot");
            }
        } catch (error) {
            appendMessage("⚠️ Error adding to cart.", "bot");
        }
    }

    document.querySelector("button").addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") sendMessage();
    });
});

if (data.product) {
    addMessage("bot", `
        <div class="product-card">
            <img src="${data.image}" class="product-image" alt="${data.product}">
            <div><strong>${data.product}</strong></div>
            <div>Price: ₹${data.price}</div>
            <div>Stock: ${data.stock}</div>
            <a href="${data.link}" target="_blank" class="buy-btn">Buy Now</a>
        </div>
    `);
}
