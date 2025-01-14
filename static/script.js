const textarea = document.getElementById("text-input");
const correctButton = document.getElementById("correct-button");
const outputSection = document.querySelector(".output-section");

const tabs = document.querySelectorAll(".tab");
const correctionsList = document.getElementById("corrections-list");

let allCorrections = [];
let capitalizationCorrections = []; 
let grammarCorrections = [];
let spellingCorrections = [];
let punctuationCorrections = [];

textarea.addEventListener("input", () => {
    outputSection.classList.add("blur");
    resetTabs();
    resetCorrections();
});

correctButton.addEventListener("click", () => {
    const textInput = textarea.value;

    // Show loader
    document.getElementById("loader").style.display = "block";

    fetch("/correct", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `text=${encodeURIComponent(textInput)}`,
    })
        .then((response) => response.json())
        .then((data) => {
            const corrections = data.corrections;
            const counts = data.counts;

            allCorrections = corrections.all;
            capitalizationCorrections = corrections.capitalization;
            grammarCorrections = corrections.grammar;
            spellingCorrections = corrections.spelling;
            punctuationCorrections = corrections.punctuation;

            // Update counts
            document.getElementById("all-count").textContent = counts.all;
            document.getElementById("capitalization-count").textContent = counts.capitalization;
            document.getElementById("grammar-count").textContent = counts.grammar;
            document.getElementById("spelling-count").textContent = counts.spelling;
            document.getElementById("punctuation-count").textContent = counts.punctuation;

            // Initially show all corrections
            updateCorrections("all", allCorrections);

            // Remove blur effect after corrections are displayed
            outputSection.classList.remove("blur");

            // Hide loader
            document.getElementById("loader").style.display = "none";

            // Display the corrected text
            document.getElementById("corrected-text").textContent = data.corrected_text;
        })
        .catch((error) => {
            // Hide loader in case of error
            document.getElementById("loader").style.display = "none";
            console.error("Error:", error);
        });
});

tabs.forEach(tab => {
    tab.addEventListener("click", () => {
        // Activate the clicked tab
        tabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        const tabName = tab.getAttribute("data-tab");
        
        // Update corrections based on the selected tab
        switch (tabName) {
            case "all":
                updateCorrections("all", allCorrections);
                break;
            case "capitalization":
                updateCorrections("capitalization", capitalizationCorrections);
                break;
            case "grammar":
                updateCorrections("grammar", grammarCorrections);
                break;
            case "spelling":
                updateCorrections("spelling", spellingCorrections);
                break;
            case "punctuation":
                updateCorrections("punctuation", punctuationCorrections);
                break;
        }
    });
});

function updateCorrections(tabName, corrections) {
    correctionsList.innerHTML = "";

    corrections.forEach(([incorrect, corrected]) => {
        const li = document.createElement("li");
        if (incorrect === " ") {
            li.innerHTML = `<span class="inserted-word">[Inserted]</span> → <span class="corrected-word">${corrected}</span>`;
        } else {
            li.innerHTML = `<span class="error-word">${incorrect}</span> → <span class="corrected-word">${corrected}</span>`;
        }
        correctionsList.appendChild(li);
    });
}

function resetTabs() {
    tabs.forEach(tab => tab.classList.remove("active"));
    document.querySelector(".tab[data-tab='all']").classList.add("active");
}

function resetCorrections() {
    correctionsList.innerHTML = "";
    document.getElementById("corrected-text").innerText = "";
}

