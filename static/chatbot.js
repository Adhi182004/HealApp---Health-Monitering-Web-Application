async function sendMessage() {
    const userMessage = document.getElementById("userMsg").value;

    const response = await fetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage })
    });

    const data = await response.json();

    document.getElementById("chatArea").innerHTML += `
        <div class="user">You: ${userMessage}</div>
        <div class="bot">HealAI: ${data.reply}</div>
    `;

    document.getElementById("userMsg").value = "";
}
