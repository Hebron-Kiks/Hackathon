console.log("✅ script.js is loaded"); // Check if script is running

document.getElementById("generateBtn").addEventListener("click", async () => {
    const notes = document.getElementById("notes").value;
    console.log("Button clicked ✅");
    console.log("Notes entered:", notes);

    if (!notes.trim()) {
        alert("⚠️ Please enter some notes before generating flashcards!");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:5000/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ notes: notes })
        });

        console.log("📡 Fetch response status:", response.status);

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        console.log("✅ Flashcards received:", data);

        const flashcardsContainer = document.getElementById("flashcards");
        flashcardsContainer.innerHTML = ""; // Clear old cards

        if (data.flashcards && data.flashcards.length > 0) {
            data.flashcards.forEach(card => {
                const cardDiv = document.createElement("div");
                cardDiv.classList.add("card");
                cardDiv.innerHTML = `
                    <div class="card-inner">
                        <div class="card-front"><p>${card.question}</p></div>
                        <div class="card-back"><p>${card.answer}</p></div>
                    </div>
                `;
                flashcardsContainer.appendChild(cardDiv);
            });
        } else {
            flashcardsContainer.innerHTML = "<p>No flashcards generated. Try again.</p>";
        }
    } catch (error) {
        console.error("❌ Error:", error);
        alert("Failed to connect to the backend. Check if Flask is running.");
    }
});
